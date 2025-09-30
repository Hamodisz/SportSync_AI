// remotion/src/VideoRoot.jsx
import React from 'react';
import {AbsoluteFill, Img, Sequence, useVideoConfig} from 'remotion';
import Lottie from 'lottie-react';

export default function VideoRoot(props) {
  // props expected: { title, subtitle, images: [ ... ], seconds, fps, lottie (optional path) }
  const { title = '', subtitle = '', images = [], seconds = 1.2, fps = 30, lottie = null } = props;
  const framesPerImage = Math.max(1, Math.round(seconds * fps));
  const totalFrames = framesPerImage * Math.max(1, images.length);

  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      {images.map((img, i) => {
        const from = i * framesPerImage;
        return (
          <Sequence key={i} from={from} durationInFrames={framesPerImage}>
            <AbsoluteFill>
              <Img src={img} style={{objectFit: 'cover', width: '100%', height: '100%'}} />
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {/* Title overlay at start */}
      <Sequence from={0} durationInFrames={Math.min(4 * fps, totalFrames)}>
        <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', pointerEvents: 'none'}}>
          <div style={{position: 'absolute', top: 120, width: '100%', textAlign: 'center'}}>
            <h1 style={{fontSize: 64, color: 'white', margin: 0, textShadow: '0 6px 24px rgba(0,0,0,0.7)'}}>{title}</h1>
          </div>
          <div style={{position: 'absolute', bottom: 120, width: '100%', textAlign: 'center'}}>
            <h3 style={{fontSize: 28, color: 'white', margin: 0, opacity: 0.95}}>{subtitle}</h3>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* optional Lottie (pass parsed JSON as props.lottie if you want it) */}
      {lottie && (
        <Sequence from={0} durationInFrames={Math.min(4 * fps, totalFrames)}>
          <AbsoluteFill style={{pointerEvents: 'none'}}>
            <div style={{position: 'absolute', left: 40, top: 40, width: 160}}>
              <Lottie animationData={lottie} loop={true} />
            </div>
          </AbsoluteFill>
        </Sequence>
      )}
    </AbsoluteFill>
  );
}
