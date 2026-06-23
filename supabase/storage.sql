-- AI Hiring Assistant - Supabase Storage Setup
-- Run these commands in the Supabase SQL Editor

-- 1. Create the resumes storage bucket
INSERT INTO storage.buckets (id, name, public, avif_autodetection)
VALUES ('resumes', 'resumes', true, false)
ON CONFLICT (id) DO NOTHING;

-- 2. Allow authenticated users to upload to resumes bucket
CREATE POLICY "Allow authenticated uploads"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'resumes' AND
    auth.role() = 'authenticated'
);

-- 3. Allow authenticated users to read their own uploads
CREATE POLICY "Allow individual read access"
ON storage.objects
FOR SELECT
TO authenticated
USING (
    bucket_id = 'resumes' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- 4. Allow public read access to all resume files
CREATE POLICY "Allow public read access"
ON storage.objects
FOR SELECT
TO public
USING (bucket_id = 'resumes');
