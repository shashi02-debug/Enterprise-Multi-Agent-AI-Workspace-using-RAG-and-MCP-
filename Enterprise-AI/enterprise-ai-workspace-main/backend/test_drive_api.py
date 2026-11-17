import asyncio
import json

import httpx

from app.mcp.google_drive import get_google_access_token


async def main():
    print("=" * 70)
    print("GOOGLE DRIVE API DIAGNOSTIC")
    print("=" * 70)

    try:
        access_token = await get_google_access_token()

        if not access_token:
            print("\n❌ No Google access token available.")
            return

        print("\n✅ Access token obtained from existing OAuth system.")

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            # ---------------------------------------------------------
            # TEST 1: Identify the Google account
            # ---------------------------------------------------------
            print("\n[1] Checking authenticated Google account...")

            about_response = await client.get(
                "https://www.googleapis.com/drive/v3/about",
                headers=headers,
                params={
                    "fields": "user(displayName,emailAddress,permissionId)"
                },
            )

            print("HTTP status:", about_response.status_code)

            if about_response.status_code != 200:
                print("\n❌ Google Drive API rejected the request.")
                print(about_response.text)
                return

            about_data = about_response.json()

            print("\n✅ Google Drive API authentication works.")
            print(
                json.dumps(
                    about_data,
                    indent=2
                )
            )

            # ---------------------------------------------------------
            # TEST 2: List a few normal Drive files
            # ---------------------------------------------------------
            print("\n[2] Listing files from normal Google Drive API...")

            files_response = await client.get(
                "https://www.googleapis.com/drive/v3/files",
                headers=headers,
                params={
                    "pageSize": 10,
                    "fields": (
                        "files("
                        "id,"
                        "name,"
                        "mimeType,"
                        "owners(emailAddress),"
                        "trashed,"
                        "createdTime,"
                        "modifiedTime"
                        ")"
                    ),
                    "orderBy": "modifiedTime desc",
                    "q": "trashed = false",
                },
            )

            print("HTTP status:", files_response.status_code)

            if files_response.status_code != 200:
                print("\n❌ Google Drive API file listing failed.")
                print(files_response.text)
                return

            files_data = files_response.json()

            files = files_data.get(
                "files",
                []
            )

            print(
                f"\n✅ Normal Google Drive API returned "
                f"{len(files)} file(s)."
            )

            if not files:
                print(
                    "\n⚠️ Google Drive API itself returned zero files."
                )
            else:
                print("\nFiles visible through normal Drive API:")

                for index, file in enumerate(
                    files,
                    start=1
                ):
                    print(
                        f"\n{index}. {file.get('name')}"
                    )
                    print(
                        f"   ID: {file.get('id')}"
                    )
                    print(
                        f"   MIME: {file.get('mimeType')}"
                    )
                    print(
                        f"   Owner: "
                        f"{file.get('owners', [{}])[0].get('emailAddress')}"
                    )

            # ---------------------------------------------------------
            # TEST 3: Specifically search for Accommodation
            # ---------------------------------------------------------
            print(
                "\n[3] Searching normal Google Drive API "
                "for 'Accommodation'..."
            )

            search_response = await client.get(
                "https://www.googleapis.com/drive/v3/files",
                headers=headers,
                params={
                    "pageSize": 10,
                    "fields": (
                        "files("
                        "id,"
                        "name,"
                        "mimeType,"
                        "owners(emailAddress),"
                        "trashed"
                        ")"
                    ),
                    "q": (
                        "trashed = false and "
                        "name contains 'Accommodation'"
                    ),
                },
            )

            print(
                "HTTP status:",
                search_response.status_code
            )

            if search_response.status_code != 200:
                print(
                    "\n❌ Accommodation search failed."
                )
                print(search_response.text)
                return

            search_data = search_response.json()

            accommodation_files = search_data.get(
                "files",
                []
            )

            print(
                f"\nAccommodation search returned "
                f"{len(accommodation_files)} file(s)."
            )

            for file in accommodation_files:
                print(
                    f"\n📄 {file.get('name')}"
                )
                print(
                    f"   ID: {file.get('id')}"
                )
                print(
                    f"   MIME: {file.get('mimeType')}"
                )

        print("\n" + "=" * 70)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 70)

    except Exception as exc:
        print("\n❌ Diagnostic failed:")
        print(type(exc).__name__)
        print(str(exc))


if __name__ == "__main__":
    asyncio.run(main())