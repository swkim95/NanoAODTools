import os
import sys

def generate_python_scripts(file_with_names_and_paths, base_output_directory):
    # Read the file containing script names and paths
    try:
        with open(file_with_names_and_paths, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: The file '{file_with_names_and_paths}' was not found.")
        return

    for idx, line in enumerate(lines):
        line = line.strip()  # Strip any extra whitespace or newlines
        # print(f"Processing line {idx + 1}: '{line}'")  # Debug: Print current line

        # Check if line is empty or malformed
        if not line:
            print(f"Warning: Empty or malformed line {idx + 1}. Skipping.")
            continue

        # Parse the line, assuming it contains "script_name, script_path"
        if ',' in line:
            script_name, script_path = line.split(',', 1)
        else:
            print(f"Error: Invalid format in line: '{line}'. Expected format: 'script_name,script_path'")
            continue

        # Debugging prints for script_name and script_path
        # print(f"Parsed script_name: '{script_name}', script_path: '{script_path}'")

        # Clean up script name and path
        process_name = script_name.strip()
        process_path = script_path.strip()

        script_name = script_name.strip()
        script_path = script_path.strip()
        # Ensure the script name has the .py extension
        if not script_name.endswith('.py'):
            script_name += '.py'
        script_name = "crab_cfg_" + script_name

        # Extract the base directory name from the script name (without .py)
        process_base_name = os.path.splitext(process_name)[0]

        base_output_name = base_output_directory.strip().replace('/','')

        # Determine the full output directory path
        full_output_directory = os.path.join(base_output_directory, process_base_name)

        # Create the output directory if it doesn't exist
        os.makedirs(full_output_directory, exist_ok=True)

        # Define the content of the Python script
        script_content = f'''# Auto-generated Python script
from WMCore.Configuration import Configuration
# from CRABClient.UserUtilities import config

config = Configuration()

config.section_("General")
config.General.requestName = '{process_name}'
config.General.transferLogs = True

config.section_("JobType")
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'PSet.py'
config.JobType.scriptExe = 'crab_script.sh'
config.JobType.inputFiles = ['crab_script.py', '../../Run2_UL_SkimList_MC.txt']

config.section_("Data")
config.Data.inputDataset = '{process_path}'
config.Data.inputDBS = 'global'
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 1
config.Data.outLFNDirBase = '/store/user/sungwon/DY_Run2_UL_NanoAOD/{base_output_name}/{process_name}'
config.Data.publication = False
config.Data.outputDatasetTag = '{process_name}'

config.section_("Site")
config.Site.storageSite = "T3_KR_KNU"
'''

        script_content_2 = f'''#!/usr/bin/env python3
import os
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import *

# this takes care of converting the input files from CRAB
from PhysicsTools.NanoAODTools.postprocessing.utils.crabhelper import inputFiles, runsAndLumis

p = PostProcessor(".",
                  inputFiles(),
                  branchsel="Run2_UL_SkimList_MC.txt",
                  provenance=True,
                  fwkJobReport=True,
                  jsonInput=runsAndLumis()) # Remove cut, add branchsel
p.run()

print("DONE")
'''

        script_content_3 = f'''#this is not mean to be run locally
#
echo Check if TTY
if [ "`tty`" != "not a tty" ]; then
  echo "YOU SHOULD NOT RUN THIS IN INTERACTIVE, IT DELETES YOUR LOCAL FILES"
else

echo "ENV..................................."
env 
echo "VOMS"
voms-proxy-info -all
echo "CMSSW BASE, python path, pwd"
echo $CMSSW_BASE 
echo $PYTHON_PATH
echo $PWD 

echo Found Proxy in: $X509_USER_PROXY
python3 crab_script.py $1
fi
'''

        script_content_4 = f'''# this fake PSET is needed for local test and for crab to figure the output
# filename you do not need to edit it unless you want to do a local test using
# a different input file than the one marked below
import FWCore.ParameterSet.Config as cms
process = cms.Process('NANO')
process.source = cms.Source(
    "PoolSource",
    fileNames=cms.untracked.vstring(),
)
process.source.fileNames = [
    '../../NanoAOD/test/lzma.root'  # you can change only this line
]
process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(-1)) # HERE : Max events -> -1
process.output = cms.OutputModule("PoolOutputModule",
                                  fileName=cms.untracked.string('tree.root')) # Do not change tree.root to other, or CRAB bug appears
process.out = cms.EndPath(process.output)
'''
        if "SingleMuon" in process_name:
            script_content = script_content.replace("Run2_UL_SkimList_MC", "Run2_UL_SkimList_Data")
            script_content_2 = script_content_2.replace("Run2_UL_SkimList_MC", "Run2_UL_SkimList_Data")

        # Link to Golden Jason 2016, 2017, and 2018 for LumiMask (UL)
        GoldenJason_2016 = "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions16/13TeV/Legacy_2016/Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt"
        GoldenJason_2017 = "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions17/13TeV/Legacy_2017/Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt"        
        GoldenJason_2018 = "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions18/13TeV/Legacy_2018/Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt"

        # Check if "2018" is in process_name and insert the URL line after the inputDataset line
        if "2016" in process_name:
            # Find the location of the 'config.Data.inputDataset' line
            insert_position = script_content.find(f"config.Data.inputDataset = '{process_path}'") + len(f"config.Data.inputDataset = '{process_path}'\n")            
            # Insert the URL line right after 'config.Data.inputDataset'
            script_content = script_content[:insert_position] + "config.Data.lumiMask = '" + GoldenJason_2016 + "'\n" + script_content[insert_position:]

        # Check if "2018" is in process_name and insert the URL line after the inputDataset line
        if "2017" in process_name:
            # Find the location of the 'config.Data.inputDataset' line
            insert_position = script_content.find(f"config.Data.inputDataset = '{process_path}'") + len(f"config.Data.inputDataset = '{process_path}'\n")            
            # Insert the URL line right after 'config.Data.inputDataset'
            script_content = script_content[:insert_position] + "config.Data.lumiMask = '" + GoldenJason_2017 + "'\n" + script_content[insert_position:]

        # Check if "2018" is in process_name and insert the URL line after the inputDataset line
        if "2018" in process_name:
            # Find the location of the 'config.Data.inputDataset' line
            insert_position = script_content.find(f"config.Data.inputDataset = '{process_path}'") + len(f"config.Data.inputDataset = '{process_path}'\n")            
            # Insert the URL line right after 'config.Data.inputDataset'
            script_content = script_content[:insert_position] + "config.Data.lumiMask = '" + GoldenJason_2018 + "'\n" + script_content[insert_position:]


        # Create the full path for the new Python file
        script_full_path   = os.path.join(full_output_directory, script_name) # crab_cfg_{process name}.py
        script_full_path_2 = os.path.join(full_output_directory, "crab_script.py") # Actual post processor defined here
        script_full_path_3 = os.path.join(full_output_directory, "crab_script.sh") # script to run crab_script.py
        script_full_path_4 = os.path.join(full_output_directory, "PSet.py") # Fake PSet, only defined output file name and # of events to process

        # Write the content to the new Python file
        with open(script_full_path, 'w') as script_file:
            script_file.write(script_content)
        print(f"Generated script: {script_full_path}")

        with open(script_full_path_2, 'w') as script_file:
            script_file.write(script_content_2)
        print(f"Generated script: {script_full_path_2}")

        with open(script_full_path_3, 'w') as script_file:
            script_file.write(script_content_3)
        print(f"Generated script: {script_full_path_3}")

        with open(script_full_path_4, 'w') as script_file:
            script_file.write(script_content_4)
        print(f"Generated script: {script_full_path_4}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_scripts.py <file_with_script_names_and_paths.txt> <base_output_directory>")
    else:
        file_with_names_and_paths = sys.argv[1]
        base_output_directory = sys.argv[2]
        generate_python_scripts(file_with_names_and_paths, base_output_directory)
