import ast
import glob
import os
import re
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import pandas as pd
from openai import OpenAI

SYSTEM_PROMPT = (
    "You are a career intelligence engine.\\n\\n"
    "You must:\\n"
    "- Analyze the given user data\\n"
    "- Compare it with hiring trends dataset\\n"
    "- Recommend optimal career path\\n\\n"
    "STRICT OUTPUT FORMAT:\\n"
    "Return output in EXACT segments separated by ';'\\n\\n"
    "Segments order:\\n"
    "1. Recommended Roles\\n"
    "2. Required Skills Gap\\n"
    "3. Project Recommendations\\n"
    "4. Resume Improvements\\n"
    "5. Company Targets\\n"
    "6. Timeline Strategy\\n\\n"
    "Keep each segment concise but precise.\\n"
    "No extra text outside segments.\\n"
    "IMPORTANT: Respond with ONLY the 6 segments separated by ';'. No JSON, no markdown, no extra text."
)

RESUME_PROMPT = (
    "You are an ATS-optimized resume generator.\\n\\n"
    "Generate a professional one-page resume with:\\n"
    "- Strong action verbs\\n"
    "- Metrics-driven bullet points\\n"
    "- Clean formatting\\n\\n"
    "Sections:\\n"
    "- Name\\n"
    "- Education\\n"
    "- Skills\\n"
    "- Projects\\n"
    "- Experience\\n"
    "- Achievements\\n\\n"
    "Tailor it EXACTLY to target roles inferred from user data.\\n\\n"
    "Ensure:\\n"
    "- ATS score > 95\\n"
    "- No fluff\\n"
    "- Industry-standard formatting\\n"
    "IMPORTANT: Return only plain structured text resume. No markdown, no JSON, no extra text."
)

def _safe_parse_skill_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip().lower() for x in value if str(x).strip()]

    text = str(value).strip()
    if not text or text == "[]":
        return []

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [str(x).strip().lower() for x in parsed if str(x).strip()]
    except Exception:
        pass

    parts = [p.strip().lower() for p in re.split(r"[,|/]", text) if p.strip()]
    return parts


def _parse_cgpa_to_float(value: object) -> Optional[float]:
    text = str(value or "").strip().lower()
    if not text:
        return None

    nums = [float(x) for x in re.findall(r"\\d+(?:\\.\\d+)?", text)]
    if not nums:
        return None

    if "-" in text and len(nums) >= 2:
        return sum(nums[:2]) / 2.0
    return nums[0]


def _infer_role_candidates_from_user_data(user_data: str, df: pd.DataFrame, top_n: int = 8) -> List[str]:
    text = user_data.lower()

    keyword_role_map: Dict[str, List[str]] = {
        "SDE": ["python", "java", "backend", "api", "microservices", "dsa", "algorithms", "software"],
        "ML Engineer": ["ml", "machine learning", "deep learning", "nlp", "pytorch", "tensorflow", "ai"],
        "Data Scientist": ["data science", "statistics", "pandas", "modeling", "analytics"],
        "Data Analyst": ["power bi", "tableau", "excel", "sql", "dashboard", "analysis"],
        "DevOps Engineer": ["docker", "kubernetes", "terraform", "jenkins", "devops", "cloud"],
        "Frontend Engineer": ["react", "javascript", "typescript", "ui", "frontend", "css"],
        "QA Engineer": ["testing", "qa", "selenium", "automation", "test cases"],
        "Business Analyst": ["business", "stakeholder", "requirements", "consulting", "analysis"],
        "Product Manager": ["product", "roadmap", "prioritization", "user story", "strategy"],
    }

    scored: List[Tuple[str, int]] = []
    for role, keywords in keyword_role_map.items():
        score = sum(1 for k in keywords if k in text)
        if score > 0:
            scored.append((role, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    role_from_user = [r for r, _ in scored]

    demand_roles = (
        df["job_role"]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda s: s.ne("")]
        )
        .value_counts()
        .head(top_n)
        .index.tolist()
    )

    merged = []
    for role in role_from_user + demand_roles:
        if role not in merged and role.lower() != "other":
            merged.append(role)

    if not merged:
        merged = ["SDE", "Data Analyst", "ML Engineer", "DevOps Engineer", "Frontend Engineer"]

    return merged[:top_n]


def load_dataset(data_dir: str = "Data") -> pd.DataFrame:
    csv_paths = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    frames = []
    for path in csv_paths:
        try:
            frames.append(pd.read_csv(path))
        except Exception:
            continue

    if not frames:
        raise ValueError("Could not load any CSV file from Data directory")

    merged = pd.concat(frames, ignore_index=True, sort=False)

    if "industry/domain" in merged.columns and "domain" not in merged.columns:
        merged = merged.rename(columns={"industry/domain": "domain"})

    required = [
        "company_name",
        "job_role",
        "required_skills",
        "cgpa_requirement",
        "salary_range",
        "domain",
    ]

    for col in required:
        if col not in merged.columns:
            merged[col] = ""

    result = merged[required].copy()
    for col in required:
        result[col] = result[col].fillna("")

    return result


@lru_cache(maxsize=1)
def _cached_context(data_signature: str, context_limit_chars: int = 7000) -> str:
    return data_signature[:context_limit_chars]


def build_context(df: pd.DataFrame, context_limit_chars: int = 7000) -> str:
    working = df.copy()
    working["job_role"] = working["job_role"].astype(str).str.strip()
    working["company_name"] = working["company_name"].astype(str).str.strip()
    working["domain"] = working["domain"].astype(str).str.strip()

    # Most common skills per role
    role_skill_counter: Dict[str, Dict[str, int]] = {}
    for _, row in working.iterrows():
        role = str(row.get("job_role", "")).strip()
        if not role:
            continue
        role_skill_counter.setdefault(role, {})
        skills = _safe_parse_skill_list(row.get("required_skills", ""))
        for skill in skills:
            role_skill_counter[role][skill] = role_skill_counter[role].get(skill, 0) + 1

    top_role_skills: List[str] = []
    for role in sorted(role_skill_counter.keys()):
        top_skills = sorted(
            role_skill_counter[role].items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]
        if top_skills:
            top_role_skills.append(f"{role}: {', '.join([s for s, _ in top_skills])}")

    # Average CGPA requirement per role
    cgpa_records = []
    for _, row in working.iterrows():
        role = str(row.get("job_role", "")).strip()
        cgpa = _parse_cgpa_to_float(row.get("cgpa_requirement", ""))
        if role and cgpa is not None:
            cgpa_records.append((role, cgpa))

    cgpa_df = pd.DataFrame(cgpa_records, columns=["job_role", "cgpa"])
    cgpa_lines: List[str] = []
    if not cgpa_df.empty:
        grouped = cgpa_df.groupby("job_role", as_index=False)["cgpa"].mean().sort_values("cgpa", ascending=False)
        for _, r in grouped.head(12).iterrows():
            cgpa_lines.append(f"{r['job_role']}: {r['cgpa']:.2f}")

    # Top companies per domain
    dom = working[(working["domain"] != "") & (working["company_name"] != "")]
    domain_company_lines: List[str] = []
    if not dom.empty:
        counts = (
            dom.groupby(["domain", "company_name"], as_index=False)
            .size()
            .rename(columns={"size": "posts"})
            .sort_values(["domain", "posts"], ascending=[True, False])
        )
        for domain, grp in counts.groupby("domain"):
            top_companies = grp.head(5)["company_name"].tolist()
            domain_company_lines.append(f"{domain}: {', '.join(top_companies)}")

    summary = (
        "Hiring Trend Summary\\n"
        "Most common required skills per role:\\n"
        + ("\\n".join(top_role_skills) if top_role_skills else "No skill trends available")
        + "\\n\\nAverage CGPA requirement per role:\\n"
        + ("\\n".join(cgpa_lines) if cgpa_lines else "No CGPA trends available")
        + "\\n\\nTop companies by domain:\\n"
        + ("\\n".join(domain_company_lines) if domain_company_lines else "No domain-company trends available")
    )

    return _cached_context(summary, context_limit_chars=context_limit_chars)


def _init_groq_client(model_name: str = "llama3-70b-8192"):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("Set GROQ_API_KEY in environment")
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")


def _validate_segmented_output(text: str, expected_segments: int = 6) -> bool:
    if not text or ";" not in text:
        return False
    parts = [p.strip() for p in text.split(";")]
    non_empty = [p for p in parts if p]
    return len(non_empty) >= expected_segments


def _call_with_retry(client, prompt: str, system_prompt: str, retries: int = 3, temperature: float = 0.2) -> str:
    response_text = ""
    for attempt in range(1, retries + 1):
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=1500
        )
        response_text = (response.choices[0].message.content or "").strip()

        if _validate_segmented_output(response_text, expected_segments=6):
            return response_text

        prompt = (
            prompt
            + "\\n\\nIMPORTANT FORMAT RETRY:\\n"
            + "Return EXACTLY 6 segments separated only by ';' and no extra prose."
        )

    # Last fallback: coerce into 6 segments
    chunks = [c.strip() for c in re.split(r"[\n;]+", response_text) if c.strip()]
    while len(chunks) < 6:
        chunks.append("Not enough signal; refine user data and rerun")
    return ";".join(chunks[:6])


def generate_career_report(
    user_data: str,
    data_dir: str = "Data",
    model_name: str = "llama3-70b-8192",
) -> str:
    df = load_dataset(data_dir=data_dir)
    context = build_context(df)
    role_candidates = _infer_role_candidates_from_user_data(user_data, df)

    client = _init_groq_client(model_name=model_name)

    user_prompt = (
        "USER DATA:\\n"
        f"{user_data}\\n\\n"
        "DATASET CONTEXT:\\n"
        f"{context}\\n\\n"
        "ROLE SEEDS (derived from user profile + dataset demand):\\n"
        f"{', '.join(role_candidates)}\\n\\n"
        "TASK:\\n"
        "Generate career recommendations aligned with dataset trends. "
        "Do not overfit to repetitive roles; include viable adjacent roles based on user profile."
    )

    return _call_with_retry(client, user_prompt, SYSTEM_PROMPT, retries=3)


def generate_resume(
    user_data: str,
    data_dir: str = "Data",
    model_name: str = "llama3-70b-8192",
) -> str:
    df = load_dataset(data_dir=data_dir)
    context = build_context(df)
    role_candidates = _infer_role_candidates_from_user_data(user_data, df)

    client = _init_groq_client(model_name)

    prompt = (
        RESUME_PROMPT
        + "\\n\\nUSER DATA:\\n"
        + f"{user_data}\\n\\n"
        + "DATASET CONTEXT:\\n"
        + f"{context}\\n\\n"
        + "TARGET ROLE CANDIDATES:\\n"
        + f"{', '.join(role_candidates)}\\n\\n"
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1800
    )
    return (response.choices[0].message.content or "").strip()


if __name__ == "__main__":
    sample = "name: Alex; cgpa: 8.2; skills: python, sql, power bi; projects: sales dashboard, churn model; aim: data role in fintech"
    try:
        print(generate_career_report(sample))
    except Exception as exc:
        print(f"Set GROQ_API_KEY and rerun: {exc}")

