import os
import shutil
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


# =========================================================
# HEADERS
# =========================================================

HEADERS = {
    "Content-Type": "application/json",

    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),

    "Referer": "https://leetcode.com/",
    "Origin": "https://leetcode.com",
    "X-CSRFToken": CSRF_TOKEN,
}


# =========================================================
# GRAPHQL REQUEST
# =========================================================

def graphql(
    operation_name,
    query,
    variables=None
):

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

    # -----------------------------------------------------
    # HTTP error
    # -----------------------------------------------------

    if response.status_code != 200:

        print(
            f"❌ LeetCode HTTP error: "
            f"{response.status_code}"
        )

        print(
            response.text[:1000]
        )

        response.raise_for_status()

    # -----------------------------------------------------
    # Convert response to JSON
    # -----------------------------------------------------

    result = response.json()

    # -----------------------------------------------------
    # GraphQL error
    # -----------------------------------------------------

    if result.get("errors"):

        print("❌ GraphQL error:")

        for error in result["errors"]:

            print(
                error.get(
                    "message",
                    error
                )
            )

        return None

    return result.get("data")


# =========================================================
# GET LOGGED-IN USER
# =========================================================

def get_user():

    print(
        "🔎 Checking LeetCode login..."
    )

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

        return None

    user_status = data.get(
        "userStatus"
    )

    if not user_status:

        print(
            "❌ userStatus was not returned."
        )

        return None

    signed_in = user_status.get(
        "isSignedIn"
    )

    username = user_status.get(
        "username"
    )

    print(
        f"🔐 Signed in: {signed_in}"
    )

    if not signed_in:

        print(
            "❌ LeetCode session is not authenticated."
        )

        return None

    if not username:

        print(
            "❌ Username is empty."
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

    return (
        data.get(
            "recentAcSubmissionList"
        ) or []
    )


# =========================================================
# GET PROBLEM NUMBER
# =========================================================

def get_problem_number(slug):

    query = """
    query questionData(
        $titleSlug: String!
    ) {

        question(
            titleSlug: $titleSlug
        ) {

            questionId
            title
            titleSlug
        }
    }
    """

    data = graphql(
        "questionData",
        query,
        {
            "titleSlug": slug
        }
    )

    if not data:

        return None

    question = data.get(
        "question"
    )

    if not question:

        return None

    return question.get(
        "questionId"
    )


# =========================================================
# GET SUBMISSION CODE
# =========================================================

def get_submission_details(
    submission_id
):

    print(
        f"   🔍 Getting code "
        f"for submission {submission_id}..."
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
# FIND EXISTING NUMBERED FOLDER
# =========================================================

def find_numbered_folder(slug):

    """
    Search for an existing folder such as:

        0141-linked-list-cycle

    for:

        linked-list-cycle
    """

    if not DESTINATION.exists():

        return None

    suffix = f"-{slug}"

    for folder in DESTINATION.iterdir():

        if not folder.is_dir():

            continue

        name = folder.name

        if name.endswith(suffix):

            prefix = name[
                :-len(suffix)
            ]

            if prefix.isdigit():

                return folder

    return None


# =========================================================
# MERGE DUPLICATE FOLDER
# =========================================================

def merge_duplicate_folder(
    old_folder,
    numbered_folder
):

    """
    Example:

        old:
        majority-element/

        numbered:
        0169-majority-element/

    Result:

        0169-majority-element/

    The old folder is completely removed.
    """

    print(
        "   🔄 Merging duplicate folder:"
    )

    print(
        f"      {old_folder.name}"
    )

    print(
        f"      → {numbered_folder.name}"
    )

    # -----------------------------------------------------
    # Make sure target folder exists
    # -----------------------------------------------------

    numbered_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Move missing files
    # -----------------------------------------------------

    for item in old_folder.iterdir():

        destination = (
            numbered_folder / item.name
        )

        if not destination.exists():

            shutil.move(
                str(item),
                str(destination)
            )

            print(
                f"      📦 Moved: "
                f"{item.name}"
            )

        else:

            print(
                f"      ⏭️ Kept existing: "
                f"{item.name}"
            )

    # -----------------------------------------------------
    # Delete old duplicate folder
    # -----------------------------------------------------

    if old_folder.exists():

        shutil.rmtree(
            old_folder
        )

        print(
            f"      🗑️ Removed duplicate: "
            f"{old_folder.name}"
        )


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)

    print(
        "🚀 LeetCode → GitHub Sync"
    )

    print("=" * 60)

    print()

    # -----------------------------------------------------
    # Authentication
    # -----------------------------------------------------

    print(
        "🔐 Connecting to LeetCode..."
    )

    username = get_user()

    if not username:

        print(
            "❌ Authentication failed."
        )

        raise SystemExit(1)

    print()

    # -----------------------------------------------------
    # Get submissions
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

        print(
            "⚠️ No accepted submissions found."
        )

        return

    # -----------------------------------------------------
    # Create destination folder
    # -----------------------------------------------------

    DESTINATION.mkdir(
        parents=True,
        exist_ok=True
    )

    synced = 0
    skipped = 0
    migrated = 0
    failed = 0

    # -----------------------------------------------------
    # Process submissions
    # -----------------------------------------------------

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
            f"   Slug: {slug}"
        )

        # -------------------------------------------------
        # Get problem number
        # -------------------------------------------------

        question_id = get_problem_number(
            slug
        )

        if not question_id:

            print(
                "   ❌ Could not determine "
                "problem number."
            )

            failed += 1

            continue

        # -------------------------------------------------
        # Format number
        #
        # 3   → 0003
        # 26  → 0026
        # 141 → 0141
        # 1000 → 1000
        # -------------------------------------------------

        problem_number = str(
            question_id
        ).zfill(4)

        numbered_name = (
            f"{problem_number}-{slug}"
        )

        numbered_folder = (
            DESTINATION / numbered_name
        )

        old_folder = (
            DESTINATION / slug
        )

        print(
            f"   📁 Target: "
            f"{numbered_name}"
        )

        # -------------------------------------------------
        # Handle old unnumbered folder
        # -------------------------------------------------

        if (
            old_folder.exists()
            and old_folder != numbered_folder
        ):

            # ---------------------------------------------
            # Both folders exist
            # ---------------------------------------------

            if numbered_folder.exists():

                merge_duplicate_folder(
                    old_folder,
                    numbered_folder
                )

                migrated += 1

            # ---------------------------------------------
            # Only old folder exists
            # ---------------------------------------------

            else:

                print(
                    "   🔄 Renaming:"
                )

                print(
                    f"      {old_folder.name}"
                )

                print(
                    f"      → "
                    f"{numbered_folder.name}"
                )

                old_folder.rename(
                    numbered_folder
                )

                migrated += 1

        # -------------------------------------------------
        # Make sure target exists
        # -------------------------------------------------

        numbered_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # -------------------------------------------------
        # Check existing solution
        # -------------------------------------------------

        existing_solution = list(
            numbered_folder.glob(
                "solution.*"
            )
        )

        if existing_solution:

            print(
                "   ⏭️ Already synced."
            )

            skipped += 1

            continue

        # -------------------------------------------------
        # Get submitted code
        # -------------------------------------------------

        details = get_submission_details(
            submission_id
        )

        if not details:

            print(
                "   ❌ Could not retrieve "
                "submission code."
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
                "   ❌ Submission code is empty."
            )

            failed += 1

            continue

        # -------------------------------------------------
        # Determine language
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
            numbered_folder
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
        # Create README if missing
        # -------------------------------------------------

        readme_file = (
            numbered_folder
            / "README.md"
        )

        if not readme_file.exists():

            readme_file.write_text(
                f"""# {title}

## LeetCode

https://leetcode.com/problems/{slug}/

## Problem Number

{question_id}

## Language

{language}

## Submission ID

{submission_id}
""",
                encoding="utf-8"
            )

            print(
                "   📄 README.md created."
            )

        else:

            print(
                "   ⏭️ Existing README kept."
            )

        synced += 1

    # -----------------------------------------------------
    # FINAL SUMMARY
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
        f"🔄 Migrated     : {migrated}"
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
