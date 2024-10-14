This is the local server part of the idapt app.
This app should allow the user to :
- add new files
- manage existing files (moving, renaming, deleting)
- search through files using full text search
- accessing existing files
Files must be stored locally in a folder on the machine. 
They will be accessed and managed via this web app that will be running in a safe docker container and served / displayed to the user in a window using Tauri.
The framework used for the frontend is next.js due to its widespread use and capabilities, it ensure it is relatively secure.

Files must be stored encrypted using an aes 128 encryption so that in the case of a hack of the local machine, the user private key is required to decrypt them.
The user must create a password on first app launch that will be used to create his private key that will then be used to decrypt the files.
The encryption must be asymetric and the public key extracted from the user private key.
The files will be decrypted on access by the user.


The app will also have a personal assistant interface so that the user will be able to talk with a local llm that will be able to access the user files.
Each file will be a text file for the moment and will need to be indexed so that the llm and user can do full text search on it to acheive RAG.
