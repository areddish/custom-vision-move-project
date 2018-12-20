# Utility for moving projects between subscriptions for Microsoft Cognitive Services - Custom Vision service.
Sample script to copy a Custom Vision project from one Subscription/Region to another.

# Running this script

To run you need three pieces of information:
From the settings page of the source Subscription (_where you want to copy *from*_)
*Source Training Key
*Source Project Id
From the settings page of the destination Subscription (_where you want to copy *to*_)
*Destination Training Key

To run the script you first install the requirements
```
pip install -r requirements.txt
```

Then run the python script with the necessary information:
```Python
python migrate_project.py -p <project id> -s <source training key> -d <destination training key>
```

This script will recreate a project with the destination training-key and download/upload all of the tags, regions, and images. It will leave you with a new project in your new subscription with no trained iterations, from here you can train a new iteration.


