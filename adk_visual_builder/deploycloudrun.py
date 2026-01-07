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

def setup_service_account(project_id):
    """Ensures the service account exists and has the necessary roles."""
    sa_name = "adkvisualbuilder"
    sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"
    
    # 1. Check if Service Account exists
    print(f"🔍 Checking if service account {sa_email} exists...")
    check_cmd = ["gcloud", "iam", "service-accounts", "describe", sa_email, f"--project={project_id}", "--format=json"]
    
    if run_command(check_cmd, "Service account not found, attempting to create...", capture=True) is None:
        print(f"🛠️ Creating service account: {sa_name}...")
        create_cmd = [
            "gcloud", "iam", "service-accounts", "create", sa_name,
            f"--display-name=ADK Visual Builder Service Account",
            f"--project={project_id}"
        ]
        run_command(create_cmd, "Failed to create service account.")
    else:
        print(f"✅ Service account {sa_name} already exists.")

    # 2. Define roles to assign
    roles = [
        "roles/cloudbuild.builds.builder",
        "roles/iam.serviceAccountUser",
        "roles/storage.admin",
        "roles/aiplatform.user",  # Vertex AI User role
        "roles/run.admin"         # Ensure it can manage Cloud Run
    ]
    
    print(f"🔐 Assigning IAM roles to {sa_email}...")
    for role in roles:
        bind_cmd = [
            "gcloud", "projects", "add-iam-policy-binding", project_id,
            f"--member=serviceAccount:{sa_email}",
            f"--role={role}",
            "--quiet"
        ]
        run_command(bind_cmd, f"Failed to assign role {role}")
    
    return sa_email

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

    # 2. Setup Service Account and Permissions
    sa_email = setup_service_account(project_id)
    if not sa_email:
        return

    # 3. Execute Deployment Command
    # Added --service_account flag to the deployment
    command = [
        "adk", "deploy", "cloud_run",
        f"--project={project_id}",
        f"--region={location}",
        f"--service_name={service_name}",
        f"--app_name={app_name}",
        f"--artifact_service_uri=memory://",
        f"--with_ui",
        agent_path,
        f"--",
        f"--service-account={sa_email}",
    ]

    print(f"🚀 Deploying agent '{app_name}' to {project_id} using {sa_email}...")
    
    # capture_output=False shows real-time logs
    success = run_command(command, "Deployment failed.", capture=False)
    
    if success:
        print("\n✨ Deployment completed successfully!")

if __name__ == "__main__":
    deploy_agent()
    
