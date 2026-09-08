/* eslint-disable jsx-a11y/prefer-tag-over-role -- An inline SVG map retains vector geometry and an accessible image role. */
import type { MapId } from './world';

/** Use world coordinates so the explorer stays visible on the extended roads. */
export function MiniMap({ map, x, z }: { map: MapId; x: number; z: number }) {
  const crossing = map === 'crossing';
  if (map === 'dotonbori') return <svg viewBox="-39 -73 78 146" role="img" aria-label="Dotonbori canal, three walkable bridges and riverside promenades">
    <rect x="-39" y="-73" width="78" height="146" fill="#1b2b37"/>
    <rect x="-8.4" y="-70" width="16.8" height="140" fill="#267b9b"/>
    {[-1,1].map((side) => <g key={side}>
      <rect x={side === -1 ? -18.8 : 8.4} y="-70" width="10.4" height="140" fill="#8c9796" opacity=".65"/>
      {Array.from({length:14},(_,i) => <rect key={i} x={side === -1 ? -30 : 20} y={-69+i*10} width="10" height="8" fill={i%3 === 0 ? '#c37b85' : '#5b6875'}/>)}
    </g>)}
    {[-48,0,48].map((z) => <g key={z} fill="#decdb2">
      <rect x="-13.5" y={z-3.8} width="27" height="7.6"/>
      {[-1,1].map((side) => <g key={side}>
        <rect x={side===-1?-13.5:8.5} y={z-(z===0?10.6:8.8)} width="5" height={z===0?21.2:17.6}/>
        {[-1,1].map((end) => <path key={end} d={`M${side*11-1} ${z+end*7}h2m-2 ${end*1.2}h2m-2 ${end*1.2}h2`} fill="none" stroke="#82745f" strokeWidth=".6"/>)}
      </g>)}
    </g>)}
    <text x="0" y="-7" textAnchor="middle" fontSize="4.7" fill="#fbe7bf">Ebisubashi</text>
    <circle cx="-19" cy="-13.5" r="2" fill="#6bbdff"><title>Glico runner</title></circle>
    <circle cx="-19" cy="20" r="2" fill="#ec675a"><title>Kani Doraku</title></circle>
    <circle cx="19" cy="40" r="2" fill="#f8c74f"><title>Don Quijote wheel — north bank, east of Ebisubashi</title></circle>
    <circle cx={x} cy={z} r="4" fill="#e8a4bf" opacity=".3"/>
    <circle cx={x} cy={z} r="1.8" fill="#ffd6e6"/>
  </svg>;
  const px = crossing ? x : 80 + x * 2, py = crossing ? z : 75 + z * 2;
  return <svg viewBox={crossing ? '-120 -125 240 235' : '0 0 160 150'} role="img" aria-label="Local navigation map">
    <defs><pattern id="mapGrid" width="16" height="16" patternUnits="userSpaceOnUse"><path d="M16 0H0V16" fill="none" stroke="#fff" strokeWidth=".3" opacity=".1"/></pattern></defs>
    <rect x={crossing ? -120 : 0} y={crossing ? -125 : 0} width={crossing ? 240 : 160} height={crossing ? 235 : 150} fill="url(#mapGrid)"/>
    {crossing ? <g>
      <path d="M-120-9H120V9H-120ZM-9-62H9V110H-9ZM-120-72H120V-62H-120ZM47-62H59V110H47ZM-71-62H-61V-9H-71Z" fill="#778190" opacity=".38"/>
      <g fill="#64716f" stroke="#92a39d" strokeWidth=".7" opacity=".65">
        <rect x="-45" y="-49" width="33" height="36" rx="2"/>
        <rect x="17" y="-49" width="30" height="36" rx="2"/>
        <rect x="59" y="-39" width="22" height="28" rx="1"/>
        <rect x="-59" y="-28" width="10" height="16" rx="1"/>
        <rect x="-107" y="25" width="58" height="22" rx="1"/>
        <rect x="-46" y="19" width="12" height="22" rx="1"/>
        <rect x="37" y="27" width="10" height="17" rx="1"/>
        <rect x="-40" y="-92" width="78" height="18" rx="2"/>
      </g>
      <path d="M-10-10L10 10M-10 10L10-10" stroke="#c6cec9" strokeWidth="2" opacity=".65"/>
      <path d="M-49 33V48H21V32" fill="none" stroke="#b4b5aa" strokeWidth="3" opacity=".65"/>
      <g><title>Hachikō Square, southwest of the crossing</title><circle cx="-20" cy="20" r="3.5" fill="#e6be78" stroke="#342f2a" strokeWidth="1"/><text x="-20" y="34" textAnchor="middle" fontSize="10" fill="#f5dab1">Hachikō</text></g>
    </g> : <g><rect x="9" y="9" width="142" height="132" rx="30" fill="#769b7a" opacity=".2"/><path d="M73 8H86V141H73ZM8 69H152V81H8Z" fill="#bec2a5" opacity=".5"/><rect x="65" y="22" width="30" height="18" fill="#ba7968" rx="2"/></g>}
    <circle cx={px} cy={py} r="12" fill="#e8a4bf" opacity=".18"/>
    <path d="M0-5L4 4L0 2L-4 4Z" transform={`translate(${px} ${py}) scale(${crossing ? 1.3 : 1})`} fill="#f6c2d5"/>
  </svg>;
}
