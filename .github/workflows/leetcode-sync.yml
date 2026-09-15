import os
import requests
from pathlib import Path


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

LEETCODE_URL = "https://leetcode.com/graphql"

SESSION = os.environ["LEETCODE_SESSION"]
CSRF_TOKEN = os.environ["LEETCODE_CSRF_TOKEN"]

DESTINATION = Path("solutions")


# ---------------------------------------------------------
# Create LeetCode session
# ---------------------------------------------------------

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

headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://leetcode.com/",
    "x-csrftoken": CSRF_TOKEN,
}


# ---------------------------------------------------------
# GraphQL request function
# ---------------------------------------------------------

def graphql(query, variables=None):

    response = session.post(
        LEETCODE_URL,
        headers=headers,
        json={
            "query": query,
            "variables": variables or {},
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        print("❌ LeetCode API error:")
        print(data["errors"])
        return None

    return data.get("data")


# ---------------------------------------------------------
# Get current user
# ---------------------------------------------------------

def get_user():

    query = """
    query {
        whoami {
            username
        }
    }
    """

    data = graphql(query)

    if not data:
        return None

    whoami = data.get("whoami")

    if not whoami:
        return None

    return whoami.get("username")


# ---------------------------------------------------------
# Get recent accepted submissions
# ---------------------------------------------------------

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
        }
    )

    if not data:
        return []

    return data.get("recentAcSubmissionList") or []


# ---------------------------------------------------------
# Get submission code
# ---------------------------------------------------------

def get_submission_details(submission_id):

    query = """
    query submissionDetails($submissionId: Int!) {

        submissionDetails(
            submissionId: $submissionId
        ) {

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
            "submissionId": int(submission_id)
        }
    )

    if not data:
        return None

    return data.get("submissionDetails")


# ---------------------------------------------------------
# Convert language to file extension
# ---------------------------------------------------------

def extension_for_language(language):

    extensions = {

        "python": "py",
        "python3": "py",

        "java": "java",

        "cpp": "cpp",
        "c++": "cpp",

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

    return extensions.get(
        language.lower(),
        "txt"
    )


# ---------------------------------------------------------
# Clean problem slug
# ---------------------------------------------------------

def clean_title(title):

    return (
        title
        .lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace(":", "")
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("🔐 Connecting to LeetCode...")

    username = get_user()

    if not username:

        print("❌ Could not get LeetCode username.")
        print()
        print("Possible reasons:")
        print("1. LEETCODE_SESSION expired")
        print("2. CSRF token expired")
        print("3. LeetCode API changed")
        print()
        return

    print(f"👤 LeetCode user: {username}")

    submissions = get_recent_submissions(username)

    print(
        f"📥 Found {len(submissions)} "
        f"recent accepted submissions"
    )

    if not submissions:

        print("⚠️ No submissions found.")

        return

    DESTINATION.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Process each submission
    # -----------------------------------------------------

    for submission in submissions:

        submission_id = submission["id"]

        title = submission["title"]

        slug = submission["titleSlug"]

        print()
        print(
            f"➡️ Processing: {title}"
        )

        problem_folder = (
            DESTINATION / slug
        )

        problem_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # -------------------------------------------------
        # Don't overwrite existing solution
        # -------------------------------------------------

        existing_files = list(
            problem_folder.iterdir()
        )

        if existing_files:

            print(
                f"   ⏭️ Already synced: {slug}"
            )

            continue

        # -------------------------------------------------
        # Get actual submitted code
        # -------------------------------------------------

        details = get_submission_details(
            submission_id
        )

        if not details:

            print(
                "   ⚠️ Could not retrieve code"
            )

            continue

        code = details.get("code")

        language = details["lang"]["name"]

        extension = extension_for_language(
            language
        )

        # -------------------------------------------------
        # Save solution
        # -------------------------------------------------

        solution_file = (
            problem_folder
            / f"solution.{extension}"
        )

        solution_file.write_text(
            code,
            encoding="utf-8"
        )

        print(
            f"   ✅ Saved: {solution_file}"
        )

        # -------------------------------------------------
        # Create README
        # -------------------------------------------------

        readme = (
            problem_folder
            / "README.md"
        )

        readme.write_text(
            f"# {title}\n\n"
            f"- **LeetCode:** "
            f"https://leetcode.com/problems/{slug}/\n"
            f"- **Language:** {language}\n"
            f"- **Submission ID:** "
            f"{submission_id}\n",
            encoding="utf-8"
        )

        print(
            f"   📄 Created README.md"
        )


# ---------------------------------------------------------
# Run
# ---------------------------------------------------------

if __name__ == "__main__":
    main()
