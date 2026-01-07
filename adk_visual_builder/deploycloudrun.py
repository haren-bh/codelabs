import os
import subprocess
import json
from dotenv import load_dotenv

def run_command(command, error_msg, capture=True):
    """Utility to run shell commands."""
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=capture)
        return result.stdout.strip() if capture else True
    except subprocess.CalledProcessError as e:
        print(f"❌ {error_msg}")
        if capture:
            print(f"Error details: {e.stderr}")
        return None

def get_project_number(project_id):
    """Retrieves the project number for a given project ID."""
    print(f"🔍 Fetching project number for: {project_id}...")
    cmd = ["gcloud", "projects", "describe", project_id, "--format=json"]
    output = run_command(cmd, "Failed to fetch project details.")
    if output:
        project_data = json.loads(output)
        return project_data.get("projectNumber")
    return None

def setup_iam_permissions(project_id, project_number):
    """Grants the default compute service account the required roles."""
    # This is the account that was causing the PERMISSION_DENIED error
    service_account = f"{project_number}-compute@developer.gserviceaccount.com"
    roles = [
        "roles/cloudbuild.builds.builder",
        "roles/iam.serviceAccountUser",
        "roles/storage.admin"
    ]
    
    print(f"🛠️  Setting up IAM permissions for {service_account}...")
    for role in roles:
        cmd = [
            "gcloud", "projects", "add-iam-policy-binding", project_id,
            f"--member=serviceAccount:{service_account}",
            f"--role={role}",
            "--quiet"
        ]
        run_command(cmd, f"Failed to assign role {role}")
    print("✅ IAM permissions updated.")

def deploy_agent():
    # 1. Load configuration
    load_dotenv()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    
    if not project_id:
        print("❌ Error: GOOGLE_CLOUD_PROJECT not found in .env file.")
        return

    # Configuration values
    location = "us-central1"
    agent_path = "./Agent1"
    service_name = "agent1service"
    app_name = "agent1app"

    # 2. Resolve Project Number and Fix Permissions
    project_number = get_project_number(project_id)
    if not project_number:
        return
    setup_iam_permissions(project_id, project_number)

    # 3. Execute Deployment Command
    command = [
        "adk", "deploy", "cloud_run",
        f"--project={project_id}",
        f"--region={location}",
        f"--service_name={service_name}",
        f"--app_name={app_name}",
        f"--artifact_service_uri=memory://",
        f"--with_ui",
        agent_path
    ]

    print(f"🚀 Deploying agent '{app_name}' to {project_id}...")
    
    # capture_output=False is used so you can see the ADK/gcloud build logs in real-time
    success = run_command(command, "Deployment failed.", capture=False)
    
    if success:
        print("\n✨ Deployment completed successfully!")

if __name__ == "__main__":
    deploy_agent()
