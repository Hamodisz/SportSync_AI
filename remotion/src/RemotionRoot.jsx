// remotion/src/RemotionRoot.jsx
import React from 'react';
import {Composition} from 'remotion';
import VideoRoot from './VideoRoot';

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="SportSyncVideo"
        component={VideoRoot}
        durationInFrames={900} /* آمن */ 
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{}}
      />
    </>
  );
};

export default RemotionRoot;
