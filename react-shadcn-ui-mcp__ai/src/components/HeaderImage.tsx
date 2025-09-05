export function HeaderImage({ src, alt }: { src: string, alt: string }) {
  return (
    <div className="w-full h-48 bg-gray-100 flex items-center justify-center rounded-t">
      <img src={src} alt={alt} className="object-cover h-full w-full rounded-t" />
    </div>
  );
}
