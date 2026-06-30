# Setup Instructions

## 1. Pinecone Setup (Vector Database)

Pinecone will store the mathematical representations (embeddings) of your PDF chunks so we can search them quickly.

1. **Create an account:** Go to [Pinecone](https://www.pinecone.io/) and sign up for a free account.
2. **Create an API Key:** 
   - Once logged in, go to the **API Keys** section on the left sidebar.
   - Create a new API Key (or copy the Default one).
   - Paste this key into your `.env` file as `PINECONE_API_KEY`.
3. **Create an Index:**
   - Go to **Indexes** and click **Create Index**.
   - **Name:** `study-buddy-index` (or whatever you prefer, just make sure it matches `PINECONE_INDEX_NAME` in your `.env`).
   - **Dimensions:** Enter `384` (This is strictly required because the `all-MiniLM-L6-v2` model outputs vectors of exactly 384 dimensions).
   - **Metric:** `cosine`.
   - Click **Create Index**.

## 2. Firebase Setup (Authentication, Database, Storage)

We are using Firebase to authenticate users, store their chat/quiz history in Firestore, and store raw PDFs in Cloud Storage.

1. **Create a Firebase Project:**
   - Go to the [Firebase Console](https://console.firebase.google.com/).
   - Click **Add project** and follow the setup wizard. You can disable Google Analytics for now.
2. **Enable Firestore Database:**
   - In the left sidebar, click **Build > Firestore Database**.
   - Click **Create database**. Start in **Test mode** (or Production mode, but remember to update security rules later). Choose a location close to you.
3. **Enable Cloudinary for PDF Storage:**
   - Since Firebase Storage may require a billing account, we use Cloudinary.
   - Go to [Cloudinary](https://cloudinary.com/) and sign up for a free account.
   - Go to your Dashboard and copy your **Cloud Name**, **API Key**, and **API Secret**.
   - Add these to your `.env` file as `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET`.
4. **Enable Authentication:**
   - In the left sidebar, click **Build > Authentication**.
   - Click **Get started**. Go to the **Sign-in method** tab.
   - Enable **Email/Password** (or Google sign-in if you prefer).
5. **Get the Service Account Key (For the Backend):**
   - Click the gear icon ⚙️ next to "Project Overview" (top left) and select **Project settings**.
   - Go to the **Service accounts** tab.
   - Click **Generate new private key**.
   - This will download a `.json` file. 
   - **CRITICAL:** Move this `.json` file into your project folder and rename it to `firebase-adminsdk.json`. **DO NOT COMMIT THIS FILE TO GITHUB**.
   - Ensure your `.env` has `FIREBASE_SERVICE_ACCOUNT_KEY_PATH=firebase-adminsdk.json`.
