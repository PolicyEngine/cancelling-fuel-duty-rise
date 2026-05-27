"use client";

import Image from "next/image";
import { useState } from "react";
import SectionHeading from "./SectionHeading";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const MEDIA_IMAGES = [
  {
    src: `${basePath}/media/itv-peston-2.png`,
    width: 1738,
    height: 1002,
    alt: "Peston programme screen referencing the fuel duty analysis.",
    caption: "On-air segment introducing the fuel-duty analysis.",
    previewClassName: "object-contain",
  },
  {
    src: `${basePath}/media/itv-peston-3.png`,
    width: 1840,
    height: 854,
    alt: "ITV Peston subtitles covering the fuel duty analysis.",
    caption: "Subtitled discussion of the fiscal estimate.",
    previewClassName: "object-contain scale-125",
  },
  {
    src: `${basePath}/media/itv-peston-1.png`,
    width: 1774,
    height: 984,
    alt: "ITV Peston episode page showing the 20 May programme details.",
    caption: "ITV Peston episode listing, 20 May broadcast.",
    previewClassName: "object-contain",
  },
];

export default function MediaCoverageTab() {
  const [selectedImage, setSelectedImage] = useState(null);

  return (
    <div className="space-y-8">
      <SectionHeading
        title="ITV Peston coverage"
        description={
          <>
            ITV&apos;s{" "}
            <a
              href="https://www.itv.com/watch/peston/2a4458/2a4458a0390"
              target="_blank"
              rel="noreferrer"
            >
              Peston
            </a>{" "}
            covered this fuel-duty analysis in the 20 May episode. The segment
            discussed the cost of cancelling the planned rise, including the
            narrower 5p-only framing used in press coverage. Peston is ITV&apos;s
            42-minute political interview programme hosted by ITV News
            Political Editor Robert Peston.
          </>
        }
      />

      <div className="grid gap-6 xl:grid-cols-3">
        {MEDIA_IMAGES.map((image) => (
          <figure
            key={image.src}
            className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
          >
            <button
              type="button"
              className="relative block aspect-video w-full bg-slate-50"
              onClick={() => setSelectedImage(image)}
              aria-label={`Expand image: ${image.caption}`}
            >
              <Image
                src={image.src}
                alt={image.alt}
                fill
                sizes="(min-width: 1280px) 33vw, 100vw"
                className={image.previewClassName}
                unoptimized
              />
            </button>
            <figcaption className="border-t border-slate-100 px-4 py-3 text-sm text-slate-600">
              {image.caption}
            </figcaption>
          </figure>
        ))}
      </div>

      {selectedImage && (
        <div
          className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-950/80 p-4"
          role="dialog"
          aria-modal="true"
          aria-label={selectedImage.caption}
          onClick={() => setSelectedImage(null)}
        >
          <div
            className="relative max-h-full w-full max-w-6xl"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="absolute right-3 top-3 z-10 rounded-full bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 shadow"
              onClick={() => setSelectedImage(null)}
            >
              Close
            </button>
            <Image
              src={selectedImage.src}
              alt={selectedImage.alt}
              width={selectedImage.width}
              height={selectedImage.height}
              className="max-h-[88vh] w-full rounded-xl object-contain"
              unoptimized
            />
          </div>
        </div>
      )}
    </div>
  );
}
