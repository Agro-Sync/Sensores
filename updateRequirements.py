import subprocess

print("Atualizando requirements.txt com pipreqs...")
subprocess.run(["pipreqs", ".", "--force", "--ignore", ".venv"])
print("Atualização concluída!")
