import React from 'react';
import {Composition} from 'remotion';
import {ShortTeaser, ShortTeaserProps, SHORT_TEASER_DURATION} from './ShortTeaser';

const defaultProps: ShortTeaserProps = {
  title: 'SportSync — Personalized Motion',
  bullets: [
    'Decode your sport identity in minutes',
    'Layer-Z insights map mindset + movement',
    'Micro-coaching prompts to keep momentum',
  ],
  footage: [
    {type: 'image', src: 'assets/images/aa_teaser01.png'},
    {type: 'image', src: 'assets/images/ab_teaser02.png'},
    {type: 'image', src: 'assets/images/ac_teaser03.png'},
  ],
  brandSignature: {
    palette: {
      background: '#0d1628',
      accent: '#5dd0ff',
      text: '#ffffff',
    },
    logo: 'assets/brand/logo.png',
    tagline: 'Layer-Z Intelligence by SportSync',
  },
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="short-teaser"
        component={ShortTeaser}
        durationInFrames={SHORT_TEASER_DURATION}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={defaultProps}
      />
    </>
  );
};
