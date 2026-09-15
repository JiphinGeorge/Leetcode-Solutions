import os
import json
import requests
from pathlib import Path


LEETCODE_URL = "https://leetcode.com/graphql"
GITHUB_REPO = os.environ["GITHUB_REPOSITORY"]

SESSION = os.environ["LEETCODE_SESSION"]
CSRF_TOKEN = os.environ["LEETCODE_CSRF_TOKEN"]

DESTINATION = Path("solutions")


headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "x-csrftoken": CSRF_TOKEN,
    "Referer": "https://leetcode.com/",
}


session = requests.Session()

session.cookies.set(
    "LEETCODE_SESSION",
    SESSION,
    domain=".leetcode.com"
)

session.cookies.set(
    "csrftoken",
    CSRF_TOKEN,
    domain=".leetcode.com"
)


def graphql(query, variables):
    response = session.post(
        LEETCODE_URL,
        headers=headers,
        json={
            "query": query,
            "variables": variables,
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise Exception(json.dumps(data["errors"], indent=2))

    return data["data"]


def get_user():
    query = """
    query globalData {
        userStatus {
            username
        }
    }
    """

    data = graphql(query, {})

    return data["userStatus"]["username"]


def get_recent_submissions(username):
    query = """
    query recentAcSubmissions(
        $username: String!,
        $limit: Int!
    ) {
        recentAcSubmissionList(
            username: $username,
            limit: $limit
        ) {
            id
            title
            titleSlug
            timestamp
        }
    }
    """

    data = graphql(
        query,
        {
            "username": username,
            "limit": 20,
        },
    )

    return data.get("recentAcSubmissionList") or []


def get_submission_details(submission_id):
    query = """
    query submissionDetails($submissionId: Int!) {
        submissionDetails(submissionId: $submissionId) {
            code
            lang {
                name
                verboseName
            }
        }
    }
    """

    data = graphql(
        query,
        {
            "submissionId": int(submission_id),
        },
    )

    return data.get("submissionDetails")


def extension_for_language(language):
    extensions = {
        "python": "py",
        "python3": "py",
        "java": "java",
        "cpp": "cpp",
        "c": "c",
        "javascript": "js",
        "typescript": "ts",
        "kotlin": "kt",
        "swift": "swift",
        "go": "go",
        "rust": "rs",
        "php": "php",
        "csharp": "cs",
        "ruby": "rb",
    }

    return extensions.get(language.lower(), "txt")


def clean_title(title):
    return (
        title.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace(":", "")
    )


def main():

    print("🔐 Connecting to LeetCode...")

    username = get_user()

    print(f"👤 LeetCode user: {username}")

    submissions = get_recent_submissions(username)

    print(f"📥 Found {len(submissions)} recent accepted submissions")

    DESTINATION.mkdir(
        parents=True,
        exist_ok=True
    )

    for submission in submissions:

        submission_id = submission["id"]
        title = submission["title"]
        slug = submission["titleSlug"]

        print(
            f"➡️ Processing: {title} "
            f"(submission {submission_id})"
        )

        problem_folder = DESTINATION / slug

        problem_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # Do not overwrite an existing solution
        existing_files = list(problem_folder.iterdir())

        if existing_files:
            print(f"   ⏭️ Already synced: {slug}")
            continue

        details = get_submission_details(
            submission_id
        )

        if not details:
            print(
                f"   ⚠️ Could not retrieve code for {title}"
            )
            continue

        code = details["code"]

        language = details["lang"]["name"]

        extension = extension_for_language(
            language
        )

        solution_file = (
            problem_folder
            / f"solution.{extension}"
        )

        solution_file.write_text(
            code,
            encoding="utf-8"
        )

        readme = problem_folder / "README.md"

        readme.write_text(
            f"# {title}\n\n"
            f"- **LeetCode:** "
            f"https://leetcode.com/problems/{slug}/\n"
            f"- **Language:** {language}\n"
            f"- **Submission ID:** {submission_id}\n",
            encoding="utf-8"
        )

        print(
            f"   ✅ Saved: {solution_file}"
        )


if __name__ == "__main__":
    main()
