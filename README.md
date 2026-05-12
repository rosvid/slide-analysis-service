# Slide Analysis Service
Copyright © 2026 Roman Svidler. Licensed under the [GNU GPLv3](LICENSE).

A Django-based headless web service for analysing presentation slides against a set of design and content rules. This software is designed to be used by external presentation training software to give automatic feedback on presentation slides.

## Features and quick facts
- Main stack: Python 3.13, Django 6, Django REST Framework 3.17.
- Analyse PowerPoint (PPT, PPTX) files.
- Checks for various rules (e.g. minimum font size, colour contrast, image quality) and returns detailed results as a JSON object.
- Multilingual support.
- Runs in Docker with an [unoserver](https://github.com/unoconv/unoserver-docker) instance for PDF conversion.
- Main API endpoints: `POST /analyse/` (upload file), `GET /rules/` (list rules).
- Architecture is designed to be extendable and easy to maintain.

## Getting Started
### 1. Clone the repository
```bash
git clone https://github.com/rosvid/slide-analysis-service.git
cd slide-analysis-service
```

### 2. Configure environment variables
Copy the example environment file and update the values as needed:
```bash
cp .env.example .env
cp app/.env.example app/.env
cp app/.env.docker.example app/.env.docker
```
Please note that there are three .env files: One in the docker-compose location and two in the app folder.

### 3. Run with Docker
The easiest way to run the service is using Docker Compose:
```bash
docker-compose up -d
```
The service will be available at `http://localhost:8000`.

Note:
- Can also be run locally (unoserver is still required for PDF conversion): See [Development](#development).
- **Font requirement:** Fonts used in presentation slides must be available for PDF conversion, unless embedded in the file. When using `unoserver-docker`, copy font files (`.ttf`/`.otf`) to the `fonts/` folder. For legal reasons, fonts are not included in this repository.

## API usage
**Endpoint:** `POST /analyse/`

**Headers:**
- `X-API-Key`: The secret API key (defined in `.env`).
- `Accept-Language`: `en` or `de`.
- Optional: Use a rules config list to check only specific rules and/or pass parameters. Include one rules form field per rule (syntax: RULE_ID or RULE_ID:VALUE, e.g. MEDIA_MAX_ANIMATIONS_PER_SLIDE, TEXT_MAX_FONTS:2).

**Body (multipart/form-data):**
- `file`: The presentation file to analyse.

Results are returned in a machine-readable JSON format for further processing in the client software.

Example response:
```json
{
   "analysis_id": "25509def-2d4f-4dd7-9f7a-2b5743e01083",
   "analysis_timestamp": "2026-05-12T15:35:40.473340",
   "file_info": {
      "file_name": "Animations_test_01.pptx",
      "file_size": "35.11 KB",
      "total_slides": 2
   },
   "summary": {
      "total_issues_found": 2,
      "slides_with_issues": 1,
      "rules_checked": [
         "MEDIA_MAX_ANIMATIONS_PER_SLIDE",
         "TEXT_MAX_FONTS"
      ]
   },
   "global_issues": [
      {
         "rule_id": "TEXT_MAX_FONTS",
         "message": "Presentation uses 3 different fonts, which exceeds the maximum allowed of 2.",
         "details": {
            "fonts_used": [
               "Times New Roman",
               "Arial",
               "Neue Haas Grotesk Text Pro"
            ],
            "max_fonts": 2
         }
      }
   ],
   "slide_results": [
      {
         "slide_number": 1,
         "has_issues": true,
         "issues": [
            {
               "rule_id": "MEDIA_MAX_ANIMATIONS_PER_SLIDE",
               "message": "Slide contains 2 animations, which exceeds the recommended maximum of 0.",
               "details": {
                  "animation_count": 2,
                  "max_animations": 0
               }
            }
         ]
      },
      {
         "slide_number": 2,
         "has_issues": false,
         "issues": []
      }
   ]
}
```

For more API examples, see `httpRequests/test-rest.example.http`. This file can also be used to test the API directly with IntelliJ's HTTP client.

## Development
### Local Setup
1. Create a virtual environment: `python -m venv .venv`
2. Activate it:
   - Windows: `.venv\Scripts\activate`
   - Linux/macOS: `source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Compile the translations: `python app/manage.py compilemessages`.
5. Start the application: `python app/manage.py runserver`

Note:
- You need to set all the required variables in the `.env` files.
- Unoserver needs to be running for PDF conversion.
- For Unit Testing run `python app/manage.py test core.tests`.

### Extending the Rule Set
- Create new Rule ID in `app/core/enums.py` with a descriptive name in English.
- Internationalisation: Mark new strings using _(...), as seen in `app/core/enums.py`. Run `python app/manage.py makemessages -l de` to create the new entries for the translations. Edit them and compile with `python app/manage.py compilemessages`.
- Add new rule class in `app/core/rules/{text,media,layout}/` inheriting from `BaseRule` and set `RULE_ID` in `app/core/enums.py`.
- Rules may accept parameters in `__init__`; `AnalyserService` supports parameterised config strings (e.g. `TEXT_MIN_FONT_SIZE:18`).
- Implement the `apply` method to check the rule against the slide content and return a `RuleResultDto` containing any violations.