'use client';
/* eslint-disable next/no-img-element -- Blender portraits are already optimized static assets; this export has no image server. */
/* eslint-disable jsx-a11y/prefer-tag-over-role -- The inline SVG minimap needs an accessible image role while retaining vector geometry. */
import { useEffect, useRef, useState } from 'react';
import { ArrowUp, Bike, CarFront, Check, ChevronRight, CircleHelp, Compass, Footprints, MapPin, Maximize, Moon, Pause, Play, Plus, Minus, RotateCcw, Settings2, Sun, Sunset, X, Zap } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import type { World, Status, TravelMode, TimeMode, MapId } from '@/lib/game/world';
const baseStatus: Status = { loading: true, progress: 0, map: 'crossing', x: 0, z: 10, speed: 0, fps: 0, clock: '17:30', phase: 'evening', error: null };

export default function Game() {
  const mount = useRef<HTMLDivElement>(null), game = useRef<World | null>(null);
  const [status, setStatus] = useState<Status>(baseStatus);
  const [travel, setTravel] = useState<TravelMode>('walk');
  const [time, setTime] = useState<TimeMode>('evening');
  const [running, setRunning] = useState(false), [paused, setPaused] = useState(false);
  const [panel, setPanel] = useState<'help' | 'settings' | 'character' | null>(null);
  const [quality, setQuality] = useState('balanced');
  const [stick, setStick] = useState({ x: 0, y: 0 });
  const joyPointer = useRef<number | null>(null);
  const [hint, setHint] = useState(true);
  const setMode = async (mode: TravelMode) => { await game.current?.setTravel(mode); if (game.current) setTravel(game.current.travel); };
  useEffect(() => {
    let cancelled = false;
    import('@/lib/game/world').then(({ World }) => {
      if (cancelled || !mount.current) return;
      try { game.current = new World(mount.current, setStatus); setQuality(game.current.quality); }
      catch (e) { console.error(e); setStatus({ ...baseStatus, loading: false, error: 'Your browser couldn’t start 3D graphics. Enable hardware acceleration and reload.' }); }
    }).catch(() => setStatus({ ...baseStatus, loading: false, error: 'The game couldn’t start. Please reload and try again.' }));
    return () => { cancelled = true; game.current?.dispose(); game.current = null; };
  }, []);
  useEffect(() => { game.current?.setPaused(paused || panel !== null); }, [paused, panel]);
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.code === 'Escape' && !panel) setPaused((p) => !p);
      if (['KeyW','KeyA','KeyS','KeyD'].includes(e.code)) setHint(false);
      if (!panel && !paused && ['Digit1','Digit2','Digit3'].includes(e.code)) void setMode((['walk','motorcycle','car'] as const)[Number(e.code.slice(-1))-1]);
    };
    window.addEventListener('keydown', key); return () => window.removeEventListener('keydown', key);
  }, [panel, paused]);
  const setLight = (mode: TimeMode) => { setTime(mode); game.current?.setTime(mode); };
  const switchMap = (id: MapId) => { if (id !== status.map) void game.current?.switchMap(id); };
  const sprint = () => { setRunning(!running); game.current?.setRunning(!running); };
  const joyMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (joyPointer.current !== e.pointerId) return;
    const rect = e.currentTarget.getBoundingClientRect();
    let x = (e.clientX - rect.left - rect.width / 2) / 38, y = (e.clientY - rect.top - rect.height / 2) / 38;
    const n = Math.hypot(x, y); if (n > 1) { x /= n; y /= n; }
    setStick({ x: x * 32, y: y * 32 }); if (game.current) game.current.joystick = { x, y }; setHint(false);
  };
  const joyEnd = () => { joyPointer.current = null; setStick({ x: 0, y: 0 }); if (game.current) game.current.joystick = { x: 0, y: 0 }; };
  const fullScreen = () => { if (document.fullscreenElement) void document.exitFullscreen().catch(() => {}); else void document.documentElement.requestFullscreen?.().catch(() => {}); };
  const PhaseIcon = status.phase === 'night' ? Moon : status.phase === 'day' ? Sun : Sunset;

  return <main className="game-shell">
    <div className="world-canvas" ref={mount} /><div className="edge-shade" />
    <header className="game-header">
      <div className="wordmark" aria-label="Shibuya Life"><span className="jp">シブヤライフ</span><strong>SHIBUYA<span>LIFE</span></strong><span className="edition">SMALL CITY. BIG STORIES.</span></div>
      <div className="location-pill glass"><span className="location-icon"><MapPin size={19}/></span><div><span className="eyebrow">TOKYO, JAPAN</span><Select value={status.map} onValueChange={(v) => switchMap(v as MapId)} disabled={status.loading}><SelectTrigger aria-label="Change map" className="map-select"><SelectValue>{status.map === 'crossing' ? 'Shibuya Crossing' : 'Yoyogi Garden'}</SelectValue></SelectTrigger><SelectContent><SelectItem value="crossing">Shibuya Crossing</SelectItem><SelectItem value="park">Yoyogi Garden</SelectItem></SelectContent></Select></div></div>
      <div className="header-actions"><div className="time-pill glass"><PhaseIcon size={21}/><div><strong>{status.clock}</strong><span>{time === 'live' ? 'TOKYO · LIVE' : status.phase === 'evening' ? 'GOLDEN HOUR' : status.phase.toUpperCase()}</span></div></div><button className="icon-button glass" aria-label={paused ? 'Resume game' : 'Pause game'} onClick={() => setPaused(!paused)}>{paused ? <Play size={19}/> : <Pause size={19}/>}</button><button className="icon-button glass" aria-label="Settings" onClick={() => setPanel('settings')}><Settings2 size={20}/></button></div>
    </header>
    <aside className="place-note"><span className="tiny-line"/><span>{status.map === 'crossing' ? 'THE CITY IS YOURS' : 'A MOMENT TO SLOW DOWN'}</span><h1>{status.map === 'crossing' ? <>Same streets.<br/><em>New stories.</em></> : <>Take the<br/><em>scenic route.</em></>}</h1><p>{status.map === 'crossing' ? 'Find your own way through Shibuya.' : 'A little green in the heart of Tokyo.'}</p></aside>
    <div className="view-tools glass"><button aria-label="Zoom in" title="Zoom in" onClick={() => game.current?.zoom(-1)}><Plus size={20}/></button><span/><button aria-label="Zoom out" title="Zoom out" onClick={() => game.current?.zoom(1)}><Minus size={20}/></button><span/><button aria-label="Recenter camera" title="Recenter camera · R" onClick={() => game.current?.recenter()}><RotateCcw size={18}/></button><span/><button aria-label="Fullscreen" title="Fullscreen" onClick={fullScreen}><Maximize size={18}/></button></div>
    {hint && !status.loading && !status.error && <div className="look-hint glass"><span className="mouse-symbol"/><span>Drag to look around <b>·</b> Scroll to zoom</span><button onClick={() => setHint(false)} aria-label="Dismiss camera hint"><X size={14}/></button></div>}
    <footer className="game-footer">
      <div className="map-and-name"><div className="minimap glass" aria-label={`Map: player at ${status.x.toFixed(0)}, ${status.z.toFixed(0)}`}>
        <svg viewBox="0 0 160 150" role="img" aria-label="Local navigation map"><defs><pattern id="mapGrid" width="16" height="16" patternUnits="userSpaceOnUse"><path d="M 16 0 L 0 0 0 16" fill="none" stroke="#ffffff" strokeWidth=".3" opacity=".1"/></pattern></defs><rect width="160" height="150" fill="url(#mapGrid)"/>
          {status.map === 'crossing' ? <g><path d="M65 0H93V150H65ZM0 61H160V87H0Z" fill="#778190" opacity=".25"/><g fill="#64716f" stroke="#92a39d" strokeWidth=".5" opacity=".6"><rect x="11" y="12" width="39" height="36" rx="3"/><rect x="105" y="9" width="40" height="40" rx="3"/><rect x="13" y="100" width="40" height="35" rx="3"/><rect x="106" y="101" width="43" height="29" rx="3"/></g><path d="M67 62L94 87M68 86L94 61" stroke="#c6cec9" strokeWidth="2" opacity=".5"/></g> : <g><rect x="9" y="9" width="142" height="132" rx="30" fill="#769b7a" opacity=".2"/><path d="M73 8H86V141H73ZM8 69H152V81H8Z" fill="#bec2a5" opacity=".5"/><rect x="65" y="22" width="30" height="18" fill="#ba7968" rx="2"/></g>}
          <circle cx={80 + status.x * (status.map === 'crossing' ? 1.25 : 2)} cy={75 + status.z * (status.map === 'crossing' ? 1.25 : 2)} r="12" fill="#e8a4bf" opacity=".14"/><path d="M0 -5L4 4L0 2L-4 4Z" transform={`translate(${80 + status.x * (status.map === 'crossing' ? 1.25 : 2)} ${75 + status.z * (status.map === 'crossing' ? 1.25 : 2)})`} fill="#f6c2d5"/>
        </svg><span className="north">N</span><span className="map-coordinate">{status.map === 'crossing' ? '35.6595° N · 139.7005° E' : 'YOYOGI · GARDEN'}</span></div>
        <button className="character-chip" onClick={() => setPanel('character')}><span className="avatar"><img src="/renders/character.webp" alt="Haru, the cap-and-backpack explorer"/></span><span><strong>Haru</strong><small>City explorer</small></span><ChevronRight size={16}/></button>
      </div>
      <div className="travel-area"><div className="mode-label"><span className="live-dot"/>{travel === 'walk' ? 'EXPLORE AT YOUR OWN PACE' : travel === 'motorcycle' ? 'TAKE THE LONG WAY HOME' : 'YOUR NEXT STOP IS UP TO YOU'}</div><div className="travel-dock glass"><ToggleGroup value={[travel]} onValueChange={(v) => { if (v[0]) void setMode(v[0] as TravelMode); }} aria-label="Travel mode" className="travel-group" disabled={status.loading}>
        <ToggleGroupItem value="walk" aria-label="Walk" className="travel-mode"><Footprints size={21}/><span>Walk</span><span className="mode-key">1</span></ToggleGroupItem><ToggleGroupItem value="motorcycle" aria-label="Ride motorcycle" className="travel-mode"><Bike size={22}/><span>Ride</span><span className="mode-key">2</span></ToggleGroupItem><ToggleGroupItem value="car" aria-label="Drive car" className="travel-mode"><CarFront size={22}/><span>Drive</span><span className="mode-key">3</span></ToggleGroupItem>
      </ToggleGroup><div className="dock-divider"/><button className={`run-button ${running ? 'active' : ''}`} onClick={sprint} disabled={travel !== 'walk'} aria-pressed={running}><Zap size={17}/><span>{running ? 'Running' : 'Run'}</span><kbd>⇧</kbd></button></div><div className="desktop-help"><span><kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> Move</span><span><kbd>SPACE</kbd> Jump</span><span><kbd>R</kbd> Recenter</span></div></div>
      <div className="footer-right"><div className="speed-readout">{travel !== 'walk' && <><strong>{status.speed.toString().padStart(2,'0')}</strong><span>KM/H</span></>}</div><button className="help-button glass" aria-label="How to play" onClick={() => setPanel('help')}><CircleHelp size={18}/><span>How to play</span></button><span className="build-label">{status.fps || '—'} FPS <b>·</b> THIRD PERSON</span></div>
    </footer>
    <div className="mobile-controls"><div className="joystick" role="application" aria-label="Movement joystick" onPointerDown={(e) => { joyPointer.current = e.pointerId; e.currentTarget.setPointerCapture(e.pointerId); joyMove(e); }} onPointerMove={joyMove} onPointerUp={joyEnd} onPointerCancel={joyEnd} onLostPointerCapture={joyEnd}><span className="joystick-cross"/><span className="joystick-knob" style={{ transform: `translate(${stick.x}px,${stick.y}px)` }}/></div><button className="jump-button glass" aria-label="Jump" onPointerDown={(e) => { e.preventDefault(); game.current?.jump(); }} disabled={travel !== 'walk'}><ArrowUp size={25}/><span>JUMP</span></button></div>
    {status.loading && <div className="loading-screen"><div className="loading-logo">SHIBUYA <em>LIFE</em></div><span className="loading-jp">いつもの街に、あたらしい物語を。</span><div className="loading-track"><span style={{ width: `${status.progress}%` }}/></div><p>{status.progress < 26 ? 'Getting your explorer ready' : 'Opening the city'}<span>{status.progress}%</span></p></div>}
    {status.error && <div className="pause-screen"><div className="pause-card glass"><Compass size={28}/><h2>A little detour</h2><p role="alert">{status.error}</p><button className="primary-button" onClick={() => location.reload()}>Try again</button></div></div>}
    {paused && !status.error && !status.loading && <div className="pause-screen"><div className="pause-card glass"><Pause size={26}/><span className="eyebrow">TAKE YOUR TIME</span><h2>The city can wait.</h2><p>Your next story is right where you left it.</p><button className="primary-button" onClick={() => setPaused(false)}><Play size={16}/>Back to Shibuya</button></div></div>}
    <Dialog open={panel !== null} onOpenChange={(v) => { if (!v) setPanel(null); }}><DialogContent className={`game-dialog ${panel === 'character' ? 'character-dialog' : ''}`}>
      <DialogTitle>{panel === 'settings' ? 'Make yourself at home' : panel === 'character' ? 'Meet Haru.' : 'Your city. Your pace.'}</DialogTitle><DialogDescription>{panel === 'settings' ? 'A little change of atmosphere.' : panel === 'character' ? 'One backpack. A whole city of possibilities.' : 'Everything you need to find your way around.'}</DialogDescription>
      {panel === 'settings' && <div className="settings-content"><span className="settings-label">Time of day</span><ToggleGroup value={[time]} onValueChange={(v) => { if (v[0]) setLight(v[0] as TimeMode); }} className="time-options" aria-label="Time of day">{([['day',Sun,'Day'],['evening',Sunset,'Evening'],['night',Moon,'Night'],['live',Compass,'Live']] as const).map(([v,Icon,label]) => <ToggleGroupItem value={v} key={v}><Icon size={20}/><span>{label}</span></ToggleGroupItem>)}</ToggleGroup><p className="setting-note">Live follows the current time in Tokyo, with gradual dawn and dusk.</p><label htmlFor="graphics-quality">Graphics</label><Select value={quality} onValueChange={(v) => { if (v) { setQuality(v); game.current?.setQuality(v as 'high'|'balanced'); } }}><SelectTrigger id="graphics-quality" className="quality-select"><SelectValue>{quality === 'balanced' ? 'Balanced · smoother on mobile' : 'High · detail & light bloom'}</SelectValue></SelectTrigger><SelectContent><SelectItem value="balanced">Balanced · smoother on mobile</SelectItem><SelectItem value="high">High · sharper detail & light bloom</SelectItem></SelectContent></Select><p className="setting-note">Camera stays in third person. Drag freely to find your angle.</p></div>}
      {panel === 'help' && <div className="help-content"><div><kbd>W A S D</kbd><span>{travel === 'walk' ? 'Walk in the direction of the camera' : 'W / S accelerate and reverse · A / D steer'}</span></div><div><kbd>SHIFT</kbd><span>Hold to run, or use the Run toggle</span></div><div><kbd>SPACE</kbd><span>Jump while exploring on foot</span></div><div><kbd>DRAG</kbd><span>Grab the scene and rotate the view</span></div><div><kbd>SCROLL</kbd><span>Zoom in and out · pinch on mobile</span></div><div><kbd>R</kbd><span>Bring the camera behind you</span></div><div><kbd>ESC</kbd><span>Pause and take a breather</span></div><p>On mobile, use the left joystick to move and drag the right side to look. Choose a location at the top to change maps.</p></div>}
      {panel === 'character' && <div className="character-details"><img src="/renders/character.webp" alt="Blender render of Haru wearing a black cap, gray hoodie, dark trousers, sneakers and backpack"/><div><span className="eyebrow">THE CITY EXPLORER</span><p>A familiar cap, favorite sneakers, and everything for the day in one backpack.</p><span className="character-tag"><Check size={14}/>Your character</span><a href="/renders/character.png" target="_blank" rel="noreferrer">View character render <ChevronRight size={14}/></a></div></div>}
    </DialogContent></Dialog>
  </main>;
}


