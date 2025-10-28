import React from 'react';
import {
  AbsoluteFill,
  Img,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  Video,
  interpolate,
  spring,
} from 'remotion';

export type FootageItem = {
  type: 'image' | 'video';
  src: string;
  startFrame?: number;
  durationInFrames?: number;
};

export type BrandSignature = {
  palette?: {
    background?: string;
    accent?: string;
    text?: string;
    overlay?: string;
  };
  logo?: string;
  tagline?: string;
};

export interface ShortTeaserProps {
  title: string;
  bullets: string[];
  footage: FootageItem[];
  brandSignature?: BrandSignature;
}

export const SHORT_TEASER_DURATION = 180; // 6 seconds @ 30 fps

const GradientOverlay: React.FC<{color: string; opacity?: number}> = ({color, opacity = 0.75}) => (
  <AbsoluteFill
    style={{
      backgroundImage: `linear-gradient(180deg, rgba(0,0,0,${opacity * 0.25}) 0%, ${color} ${opacity * 100}%)`,
      mixBlendMode: 'multiply',
    }}
  />
);

const LogoBlock: React.FC<{logo?: string; tagline?: string; textColor: string}> = ({logo, tagline, textColor}) => {
  if (!logo && !tagline) {
    return null;
  }

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-start',
        alignItems: 'flex-start',
        padding: 48,
        gap: 24,
      }}
    >
      {logo ? (
        <Img
          src={logo}
          style={{
            width: 220,
            height: 'auto',
            objectFit: 'contain',
            filter: 'drop-shadow(0 8px 24px rgba(0,0,0,0.35))',
          }}
        />
      ) : null}
      {tagline ? (
        <div
          style={{
            color: textColor,
            fontSize: 28,
            fontWeight: 500,
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}
        >
          {tagline}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

const BulletLine: React.FC<{text: string; index: number; color: string; accent: string; totalSlides: number}> = ({
  text,
  index,
  color,
  accent,
  totalSlides,
}) => {
  const {fps} = useVideoConfig();
  const frame = useCurrentFrame();
  const slideDuration = Math.floor((SHORT_TEASER_DURATION - fps) / Math.max(1, totalSlides));
  const startFrame = index * slideDuration;
  const relativeFrame = Math.max(0, frame - startFrame);

  const entrance = spring({
    frame: relativeFrame,
    fps,
    damping: 18,
    mass: 0.6,
  });

  const opacity = interpolate(entrance, [0, 0.15, 1], [0, 0.7, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const translate = interpolate(entrance, [0, 1], [32, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <Sequence from={startFrame} durationInFrames={slideDuration}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          color,
          opacity,
          transform: `translateY(${translate}px)`,
        }}
      >
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: '999px',
            backgroundColor: accent,
            boxShadow: `0 0 18px ${accent}55`,
          }}
        />
        <div style={{fontSize: 46, lineHeight: 1.2, maxWidth: 960}}>{text}</div>
      </div>
    </Sequence>
  );
};

export const ShortTeaser: React.FC<ShortTeaserProps> = ({
  title,
  bullets,
  footage,
  brandSignature,
}) => {
  const palette = brandSignature?.palette ?? {};
  const background = palette.background ?? '#0d1628';
  const accent = palette.accent ?? '#5dd0ff';
  const textColor = palette.text ?? '#ffffff';
  const overlayColor = palette.overlay ?? 'rgba(13,22,40,0.82)';
  const totalSlides = Math.max(1, bullets.length);

  const media = footage.length > 0 ? footage : [{type: 'image' as const, src: 'assets/images/aa_teaser01.png'}];

  return (
    <AbsoluteFill style={{backgroundColor: background, fontFamily: '"Inter", "DejaVu Sans", sans-serif'}}>
      {media.map((item, idx) => {
        const duration = item.durationInFrames ?? Math.ceil(SHORT_TEASER_DURATION / media.length);
        const start = item.startFrame ?? Math.floor(idx * SHORT_TEASER_DURATION / media.length);
        const commonStyle: React.CSSProperties = {
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          filter: 'saturate(1.1) brightness(0.95)',
        };

        return (
          <Sequence key={`${item.src}-${idx}`} from={start} durationInFrames={duration}>
            {item.type === 'video' ? (
              <Video src={item.src} style={commonStyle} muted />
            ) : (
              <Img src={item.src} style={commonStyle} />
            )}
            <GradientOverlay color={overlayColor} opacity={0.85} />
          </Sequence>
        );
      })}

      <LogoBlock logo={brandSignature?.logo} tagline={brandSignature?.tagline} textColor={textColor} />

      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          padding: '0 120px',
          gap: 48,
        }}
      >
        <div
          style={{
            color: textColor,
            fontSize: 86,
            fontWeight: 700,
            letterSpacing: '-0.5px',
            textAlign: 'center',
            textShadow: '0 18px 36px rgba(0,0,0,0.45)',
          }}
        >
          {title}
        </div>

        <div style={{display: 'flex', flexDirection: 'column', gap: 28}}>
          {bullets.length === 0 ? (
            <div style={{color: textColor, opacity: 0.75, fontSize: 42}}>Drop your key benefits here.</div>
          ) : (
            bullets.map((bullet, index) => (
              <BulletLine
                key={index}
                text={bullet}
                index={index}
                color={textColor}
                accent={accent}
                totalSlides={totalSlides}
              />
            ))
          )}
        </div>
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          justifyContent: 'flex-end',
          alignItems: 'flex-end',
          padding: 48,
          color: `${textColor}cc`,
          fontSize: 28,
          letterSpacing: '0.08em',
        }}
      >
        <div>SportSync • Layer-Z Intelligence</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
