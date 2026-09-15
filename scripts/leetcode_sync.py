import os
import requests
from pathlib import Path


# =========================================================
# CONFIGURATION
# =========================================================

LEETCODE_GRAPHQL = "https://leetcode.com/graphql/"

SESSION = os.environ["LEETCODE_SESSION"]
CSRF_TOKEN = os.environ["LEETCODE_CSRF_TOKEN"]

DESTINATION = Path("solutions")


# =========================================================
# LEETCODE SESSION
# =========================================================

session = requests.Session()

# LeetCode login cookies
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


# Headers used for LeetCode GraphQL requests
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://leetcode.com/",
    "Origin": "https://leetcode.com",
    "X-CSRFToken": CSRF_TOKEN,
}


# =========================================================
# GRAPHQL REQUEST
# =========================================================

def graphql(operation_name, query, variables=None):

    payload = {
        "operationName": operation_name,
        "query": query,
        "variables": variables or {},
    }

    response = session.post(
        LEETCODE_GRAPHQL,
        headers=HEADERS,
        json=payload,
        timeout=30,
    )

    # Print useful information if LeetCode rejects request
    if response.status_code != 200:

        print(
            f"❌ LeetCode returned HTTP "
            f"{response.status_code}"
        )

        print(
            "Response:"
        )

        print(
            response.text[:1000]
        )

        response.raise_for_status()

    data = response.json()

    # GraphQL-level errors
    if data.get("errors"):

        print("❌ GraphQL error:")

        for error in data["errors"]:
            print(
                error.get("message", error)
            )

        return None

    return data.get("data")


# =========================================================
# GET LOGGED-IN USER
# =========================================================

def get_user():

    print("🔎 Checking LeetCode login...")

    query = """
    query globalData {
        userStatus {
            userId
            username
            isPremium
            activeSessionId
            isSignedIn
        }
    }
    """

    data = graphql(
        "globalData",
        query
    )

    if not data:

        print(
            "❌ No data returned from LeetCode."
        )

        return None

    user_status = data.get(
        "userStatus"
    )

    if not user_status:

        print(
            "❌ LeetCode did not return userStatus."
        )

        return None

    is_signed_in = user_status.get(
        "isSignedIn"
    )

    username = user_status.get(
        "username"
    )

    print(
        f"🔐 Signed in: {is_signed_in}"
    )

    if not is_signed_in:

        print(
            "❌ LeetCode session is not authenticated."
        )

        return None

    if not username:

        print(
            "❌ LeetCode username is empty."
        )

        return None

    print(
        f"👤 LeetCode user: {username}"
    )

    return username


# =========================================================
# GET RECENT ACCEPTED SUBMISSIONS
# =========================================================

def get_recent_submissions(username):

    print(
        "📥 Getting recent accepted submissions..."
    )

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
        "recentAcSubmissions",
        query,
        {
            "username": username,
            "limit": 20,
        }
    )

    if not data:

        return []

    submissions = data.get(
        "recentAcSubmissionList"
    )

    if not submissions:

        return []

    return submissions


# =========================================================
# GET SUBMISSION CODE
# =========================================================

def get_submission_details(
    submission_id
):

    print(
        f"   🔍 Getting code for "
        f"submission {submission_id}..."
    )

    query = """
    query submissionDetails(
        $submissionId: Int!
    ) {
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
        "submissionDetails",
        query,
        {
            "submissionId": int(
                submission_id
            )
        }
    )

    if not data:

        return None

    return data.get(
        "submissionDetails"
    )


# =========================================================
# LANGUAGE → FILE EXTENSION
# =========================================================

def extension_for_language(
    language
):

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

        "golang": "go",

        "rust": "rs",

        "php": "php",

        "csharp": "cs",
        "c#": "cs",

        "ruby": "rb",

        "scala": "scala",

        "mysql": "sql",

        "bash": "sh",
    }

    return extensions.get(
        language.lower(),
        "txt"
    )


# =========================================================
# MAIN SYNC FUNCTION
# =========================================================

def main():

    print("=" * 60)

    print(
        "🚀 LeetCode → GitHub Sync"
    )

    print("=" * 60)

    print()

    # -----------------------------------------------------
    # Step 1: Check authentication
    # -----------------------------------------------------

    print(
        "🔐 Connecting to LeetCode..."
    )

    username = get_user()

    if not username:

        print()

        print(
            "❌ Could not authenticate "
            "with LeetCode."
        )

        print(
            "Please check your GitHub secrets."
        )

        raise SystemExit(1)

    print()

    # -----------------------------------------------------
    # Step 2: Get submissions
    # -----------------------------------------------------

    submissions = get_recent_submissions(
        username
    )

    print()

    print(
        f"📊 Found {len(submissions)} "
        f"recent accepted submissions."
    )

    if not submissions:

        print()

        print(
            "⚠️ No accepted submissions "
            "were returned."
        )

        return

    # -----------------------------------------------------
    # Step 3: Create destination folder
    # -----------------------------------------------------

    DESTINATION.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Step 4: Process submissions
    # -----------------------------------------------------

    synced = 0
    skipped = 0
    failed = 0

    for submission in submissions:

        submission_id = submission[
            "id"
        ]

        title = submission[
            "title"
        ]

        slug = submission[
            "titleSlug"
        ]

        print()

        print(
            f"➡️ {title}"
        )

        print(
            f"   Submission ID: "
            f"{submission_id}"
        )

        # -------------------------------------------------
        # Create problem folder
        # -------------------------------------------------

        problem_folder = (
            DESTINATION / slug
        )

        problem_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # -------------------------------------------------
        # Check whether already synced
        # -------------------------------------------------

        existing_solution_files = []

        for file in problem_folder.iterdir():

            if file.is_file() and (
                file.name.startswith(
                    "solution."
                )
            ):

                existing_solution_files.append(
                    file
                )

        if existing_solution_files:

            print(
                "   ⏭️ Already synced."
            )

            skipped += 1

            continue

        # -------------------------------------------------
        # Get submission code
        # -------------------------------------------------

        details = get_submission_details(
            submission_id
        )

        if not details:

            print(
                "   ❌ Could not get "
                "submission details."
            )

            failed += 1

            continue

        code = details.get(
            "code"
        )

        language_info = details.get(
            "lang"
        )

        if not code:

            print(
                "   ❌ Submission code "
                "is empty."
            )

            failed += 1

            continue

        # -------------------------------------------------
        # Get language
        # -------------------------------------------------

        if language_info:

            language = language_info.get(
                "name",
                "unknown"
            )

        else:

            language = "unknown"

        extension = (
            extension_for_language(
                language
            )
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
            f"   💾 Saved: "
            f"{solution_file}"
        )

        # -------------------------------------------------
        # Create README
        # -------------------------------------------------

        readme_file = (
            problem_folder
            / "README.md"
        )

        readme_content = f"""# {title}

## LeetCode

https://leetcode.com/problems/{slug}/

## Language

{language}

## Submission ID

{submission_id}

"""

        readme_file.write_text(
            readme_content,
            encoding="utf-8"
        )

        print(
            "   📄 README.md created."
        )

        synced += 1

    # -----------------------------------------------------
    # Final summary
    # -----------------------------------------------------

    print()

    print("=" * 60)

    print(
        "📋 SYNC SUMMARY"
    )

    print("=" * 60)

    print(
        f"✅ Newly synced : {synced}"
    )

    print(
        f"⏭️ Already synced: {skipped}"
    )

    print(
        f"❌ Failed       : {failed}"
    )

    print("=" * 60)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()
