import os
import re
import shutil
import requests
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

LEETCODE_GRAPHQL = "https://leetcode.com/graphql/"
DESTINATION = Path("solutions")

LEETCODE_SESSION = os.getenv("LEETCODE_SESSION")
LEETCODE_CSRF_TOKEN = os.getenv("LEETCODE_CSRF_TOKEN")

if not LEETCODE_SESSION or not LEETCODE_CSRF_TOKEN:
    raise Exception("❌ LeetCode secrets are missing.")


# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.cookies.set(
    "LEETCODE_SESSION",
    LEETCODE_SESSION,
    domain=".leetcode.com"
)

session.cookies.set(
    "csrftoken",
    LEETCODE_CSRF_TOKEN,
    domain=".leetcode.com"
)

session.headers.update({
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Referer": "https://leetcode.com/",
    "Origin": "https://leetcode.com",
    "X-CSRFToken": LEETCODE_CSRF_TOKEN,
})


# ============================================================
# GRAPHQL HELPER
# ============================================================

def graphql(operation_name, query, variables=None):

    payload = {
        "operationName": operation_name,
        "query": query,
        "variables": variables or {}
    }

    response = session.post(
        LEETCODE_GRAPHQL,
        json=payload,
        timeout=30
    )

    if response.status_code != 200:
        print("❌ GraphQL HTTP Error:", response.status_code)
        print(response.text[:1000])
        return None

    data = response.json()

    if data.get("errors"):
        print("❌ GraphQL Error:")
        print(data["errors"])
        return None

    return data.get("data")


# ============================================================
# GET LOGGED-IN USER
# ============================================================

def get_user():

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

    data = graphql("globalData", query)

    if not data:
        return None

    return data.get("userStatus")


# ============================================================
# GET RECENT ACCEPTED SUBMISSIONS
# ============================================================

def get_recent_submissions(username):

    query = """
    query recentAcSubmissions($username: String!, $limit: Int!) {
        recentAcSubmissionList(username: $username, limit: $limit) {
            id
            title
            titleSlug
            timestamp
        }
    }
    """

    variables = {
        "username": username,
        "limit": 20
    }

    data = graphql(
        "recentAcSubmissions",
        query,
        variables
    )

    if not data:
        return []

    return data.get("recentAcSubmissionList", [])


# ============================================================
# GET QUESTION NUMBER
# ============================================================

def get_problem_number(slug):

    query = """
    query questionData($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            questionId
        }
    }
    """

    variables = {
        "titleSlug": slug
    }

    data = graphql(
        "questionData",
        query,
        variables
    )

    if not data or not data.get("question"):
        return None

    return data["question"].get("questionId")


# ============================================================
# GET SUBMISSION DETAILS
#
# IMPORTANT:
# We retrieve runtime/memory information here so that the
# GitHub commit message can use the OLD FORMAT.
# ============================================================

def get_submission_details(submission_id):

    query = """
    query submissionDetails($submissionId: Int!) {
        submissionDetails(submissionId: $submissionId) {
            code

            lang {
                name
                verboseName
            }

            runtime
            runtimeDisplay
            memory
            memoryDisplay

            runtimePercentile
            memoryPercentile
        }
    }
    """

    variables = {
        "submissionId": int(submission_id)
    }

    data = graphql(
        "submissionDetails",
        query,
        variables
    )

    if not data:
        return None

    return data.get("submissionDetails")


# ============================================================
# LANGUAGE → FILE EXTENSION
# ============================================================

LANGUAGE_EXTENSIONS = {

    "python": ".py",
    "python3": ".py",

    "java": ".java",

    "cpp": ".cpp",
    "c++": ".cpp",

    "c": ".c",

    "javascript": ".js",
    "typescript": ".ts",

    "kotlin": ".kt",

    "swift": ".swift",

    "go": ".go",

    "rust": ".rs",

    "ruby": ".rb",

    "php": ".php",

    "scala": ".scala",

    "dart": ".dart",

    "csharp": ".cs",
    "c#": ".cs",
}


# ============================================================
# CLEAN TITLE
# ============================================================

def clean_title(title):

    title = title.lower()

    title = re.sub(
        r"[^a-z0-9]+",
        "-",
        title
    )

    title = title.strip("-")

    return title


# ============================================================
# CREATE NUMBERED FOLDER NAME
# ============================================================

def create_folder_name(question_id, title):

    number = str(question_id).zfill(4)

    clean = clean_title(title)

    return f"{number}-{clean}"


# ============================================================
# FIND OLD UNNUMBERED DUPLICATE
#
# Example:
#
# Old:
# merge-sorted-array/
#
# New:
# 0088-merge-sorted-array/
#
# We migrate the contents and remove the duplicate folder.
# ============================================================

def merge_duplicate_folder(numbered_folder, title):

    old_folder = DESTINATION / clean_title(title)

    if (
        old_folder.exists()
        and old_folder.is_dir()
        and old_folder != numbered_folder
    ):

        print(
            f"🔄 Duplicate folder found: "
            f"{old_folder.name}"
        )

        numbered_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # Move files from old folder into numbered folder
        for item in old_folder.iterdir():

            destination = numbered_folder / item.name

            if destination.exists():
                continue

            shutil.move(
                str(item),
                str(destination)
            )

        # Remove the old folder completely
        shutil.rmtree(old_folder)

        print(
            f"   ✅ Removed duplicate: "
            f"{old_folder.name}"
        )

        return True

    return False


# ============================================================
# SAVE SOLUTION
# ============================================================

def save_solution(
    submission,
    details,
    question_id
):

    title = submission["title"]
    slug = submission["titleSlug"]

    folder_name = create_folder_name(
        question_id,
        title
    )

    folder = DESTINATION / folder_name

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Language
    # --------------------------------------------------------

    language = "unknown"

    if details.get("lang"):
        language = (
            details["lang"].get("name")
            or details["lang"].get("verboseName")
            or "unknown"
        )

    language_lower = language.lower()

    extension = LANGUAGE_EXTENSIONS.get(
        language_lower,
        ".txt"
    )

    # --------------------------------------------------------
    # Code
    # --------------------------------------------------------

    code = details.get("code", "")

    if not code:
        print(
            f"⚠️ No code found for {title}"
        )
        return False

    solution_file = folder / f"solution{extension}"

    # --------------------------------------------------------
    # Check if this exact solution already exists
    # --------------------------------------------------------

    if solution_file.exists():

        existing_code = solution_file.read_text(
            encoding="utf-8"
        )

        if existing_code.strip() == code.strip():

            return False

    # --------------------------------------------------------
    # Save solution
    # --------------------------------------------------------

    solution_file.write_text(
        code,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # README
    # --------------------------------------------------------

    readme_file = folder / "README.md"

    if not readme_file.exists():

        readme_content = f"""# {title}

- **LeetCode:** Problem #{question_id}
- **Language:** {language}
- **Difficulty:** Automatically synced from LeetCode
- **Problem:** https://leetcode.com/problems/{slug}/

## Solution

The solution is automatically synchronized from LeetCode.
"""

        readme_file.write_text(
            readme_content,
            encoding="utf-8"
        )

    print(
        f"✅ Saved: "
        f"{folder_name}/solution{extension}"
    )

    return True


# ============================================================
# CREATE OLD-STYLE COMMIT MESSAGE
#
# Example:
#
# [LeetCode Sync] Runtime - 0 ms (100.00%), Memory - 19.2 MB (58.28%)
# ============================================================

def create_commit_message(details):

    runtime_display = details.get(
        "runtimeDisplay"
    )

    memory_display = details.get(
        "memoryDisplay"
    )

    runtime_percentile = details.get(
        "runtimePercentile"
    )

    memory_percentile = details.get(
        "memoryPercentile"
    )

    # --------------------------------------------------------
    # Runtime
    # --------------------------------------------------------

    if not runtime_display:

        runtime = details.get("runtime")

        if runtime is not None:
            runtime_display = f"{runtime} ms"
        else:
            runtime_display = "N/A"

    # --------------------------------------------------------
    # Memory
    # --------------------------------------------------------

    if not memory_display:

        memory = details.get("memory")

        if memory is not None:
            memory_display = f"{memory} MB"
        else:
            memory_display = "N/A"

    # --------------------------------------------------------
    # Percentiles
    # --------------------------------------------------------

    if runtime_percentile is not None:

        runtime_percentile_text = (
            f"{float(runtime_percentile):.2f}%"
        )

    else:
        runtime_percentile_text = "N/A"

    if memory_percentile is not None:

        memory_percentile_text = (
            f"{float(memory_percentile):.2f}%"
        )

    else:
        memory_percentile_text = "N/A"

    # --------------------------------------------------------
    # OLD FORMAT
    # --------------------------------------------------------

    commit_message = (
        f"[LeetCode Sync] "
        f"Runtime - {runtime_display} "
        f"({runtime_percentile_text}), "
        f"Memory - {memory_display} "
        f"({memory_percentile_text})"
    )

    return commit_message


# ============================================================
# MAIN
# ============================================================

def main():

    print("🚀 Starting LeetCode Sync...\n")

    # --------------------------------------------------------
    # Authenticate
    # --------------------------------------------------------

    user = get_user()

    if not user:
        raise Exception(
            "❌ Unable to authenticate with LeetCode."
        )

    if not user.get("isSignedIn"):
        raise Exception(
            "❌ LeetCode session is not signed in."
        )

    username = user.get("username")

    print(
        f"🔐 Signed in: "
        f"{user.get('isSignedIn')}"
    )

    print(
        f"👤 LeetCode user: "
        f"{username}"
    )

    # --------------------------------------------------------
    # Get submissions
    # --------------------------------------------------------

    submissions = get_recent_submissions(
        username
    )

    print(
        f"📊 Found {len(submissions)} "
        f"recent accepted submissions."
    )

    if not submissions:
        print("ℹ️ No submissions found.")
        return

    DESTINATION.mkdir(
        parents=True,
        exist_ok=True
    )

    synced = 0
    already_synced = 0
    failed = 0
    migrated = 0

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Store the commit message of the newest newly synced
    # submission.
    #
    # Usually there will be only one new submission since
    # the previous scheduled run.
    # --------------------------------------------------------

    newest_commit_message = None

    # --------------------------------------------------------
    # Process submissions
    # --------------------------------------------------------

    for submission in submissions:

        title = submission.get(
            "title",
            "Unknown Problem"
        )

        slug = submission.get(
            "titleSlug"
        )

        submission_id = submission.get(
            "id"
        )

        print(
            f"\n🔍 Processing: "
            f"{title}"
        )

        if not slug or not submission_id:

            print(
                "❌ Missing submission information."
            )

            failed += 1
            continue

        # ----------------------------------------------------
        # Get problem number
        # ----------------------------------------------------

        question_id = get_problem_number(
            slug
        )

        if not question_id:

            print(
                f"❌ Could not find problem number "
                f"for {title}"
            )

            failed += 1
            continue

        # ----------------------------------------------------
        # Get submission details
        # ----------------------------------------------------

        details = get_submission_details(
            submission_id
        )

        if not details:

            print(
                f"❌ Could not get submission details "
                f"for {title}"
            )

            failed += 1
            continue

        # ----------------------------------------------------
        # Numbered folder
        # ----------------------------------------------------

        folder_name = create_folder_name(
            question_id,
            title
        )

        numbered_folder = (
            DESTINATION / folder_name
        )

        # ----------------------------------------------------
        # Remove/migrate old unnumbered duplicate
        # ----------------------------------------------------

        if merge_duplicate_folder(
            numbered_folder,
            title
        ):

            migrated += 1

        # ----------------------------------------------------
        # Save solution
        # ----------------------------------------------------

        try:

            saved = save_solution(
                submission,
                details,
                question_id
            )

            if saved:

                synced += 1

                # --------------------------------------------
                # Create old-style commit message
                # --------------------------------------------

                newest_commit_message = (
                    create_commit_message(
                        details
                    )
                )

                print(
                    f"📝 Commit message:\n"
                    f"   {newest_commit_message}"
                )

            else:

                already_synced += 1

        except Exception as e:

            print(
                f"❌ Failed to save {title}: "
                f"{e}"
            )

            failed += 1

    # --------------------------------------------------------
    # WRITE COMMIT MESSAGE FOR GITHUB ACTION
    # --------------------------------------------------------

    if newest_commit_message:

        commit_file = Path(
            "commit_message.txt"
        )

        commit_file.write_text(
            newest_commit_message,
            encoding="utf-8"
        )

        print(
            "\n📝 Commit message prepared."
        )

    else:

        # Remove old commit message file if there
        # are no new solutions.
        commit_file = Path(
            "commit_message.txt"
        )

        if commit_file.exists():
            commit_file.unlink()

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 50)
    print("📋 SYNC SUMMARY")
    print("=" * 50)

    print(
        f"✅ Synced       : {synced}"
    )

    print(
        f"✔️ Already synced: {already_synced}"
    )

    print(
        f"🔄 Migrated     : {migrated}"
    )

    print(
        f"❌ Failed       : {failed}"
    )

    print("=" * 50)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
