# Define the name of the virtual environment
$envName = ".venv"

# Check if the virtual environment directory exists
if (-Not (Test-Path $envName)) {
    # Create the virtual environment
    python -m venv $envName
}

# Activate the virtual environment
. .\$envName\Scripts\Activate.ps1

# Install dependencies from requirements.txt
pip install -r requirements.txt

Write-Host "Environment setup complete." -ForegroundColor Green

