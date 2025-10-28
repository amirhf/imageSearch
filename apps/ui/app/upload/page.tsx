import UploadDropzone from '@/components/UploadDropzone'

export const metadata = {
  title: 'Upload • Image Search'
}

export default function UploadPage() {
  return (
    <main className="space-y-6">
      <h1 className="text-xl font-semibold">Upload image</h1>
      <UploadDropzone />
    </main>
  )
}
