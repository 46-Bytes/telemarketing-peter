# Setting up Cloudinary for Ebook Storage

This project now uses Cloudinary for storing and serving ebooks instead of the local file system.

## Setup Instructions

1. Create a Cloudinary account at [https://cloudinary.com/](https://cloudinary.com/) if you don't have one already.

2. Once you have an account, navigate to the Dashboard to find your account details.

3. Add the following environment variables to your `.env` file:

```
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

Replace `your_cloud_name`, `your_api_key`, and `your_api_secret` with your actual Cloudinary credentials.

4. Restart the application for the changes to take effect.

## How It Works

- When an ebook is uploaded, it's temporarily stored on the server and then uploaded to Cloudinary.
- The Cloudinary URL is stored in the database instead of a local file path.
- When sending an ebook via email, the Cloudinary URL is used directly.

## Benefits

- No need to manage local file storage
- Better scalability
- Faster delivery through Cloudinary's CDN
- Automatic optimization for different devices

## Migrating Existing Ebooks

If you have existing ebooks stored in the local file system, you'll need to manually upload them to Cloudinary and update the database references. 