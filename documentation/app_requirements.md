This is the local server part of the idapt app.
This app should allow the user to :
- add new files
- manage existing files (moving, renaming, deleting)
- search through files using full text search
- accessing existing files
Files must be stored locally in a folder on the machine. 
They will be accessed and managed via this web app that will be running on the machine.
The framework used for the frontend is next.js due to its widespread use and capabilities, it ensures it is relatively secure.
Tailwind css will also be used.
The app will use mongodb for storing the files and for searchable encryption so that the implementation is easy, safe and straightforward.
Files must be stored encrypted using an searchable symetric encryption so that data is encrypted at rest on the drives and we can stil do searches over them efficiently without having to decrypt all the data.
The searchable symmetric encryption scheme need to be balanced between security and efficiency.
The user must create a password on first app launch that will be used to create his private key that will then be used to decrypt the files.
The private key must be managed very securely during app runtime and not stored when the app is turned off.
The backend part of this app should be containerized inside a docker container to ensure security and reliability.
The app will be accessed via the browser at localhost:4231.

The app will also have a personal assistant interface so that the user will be able to talk with a local llm that will be able to access the user files.
Each file will be a text file for the moment and will need to be indexed using sse so that the llm and user can do full text search on it to acheive an efficient RAG.
