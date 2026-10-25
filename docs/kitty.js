/**
 * Kitty AI — Procedural Vector Canvas Engine & Companion Simulator
 * Replicates the PyQt6 QPainter rendering from KittyAI/ui/pet_window.py 1:1 in Web Canvas.
 */

// -----------------------------------------------------------------------------
// 1. Breed / Coat Color Definitions
// -----------------------------------------------------------------------------
const COAT_SKINS = {
  black: {
    name: "Midnight Black Cat",
    body: "#1c1c22",
    belly: "#2d2d38",
    eyes: "#f2c14e",
    nose: "#d98a9a",
    pattern: "none",
    patternColor: "#111115",
    points: null
  },
  orange: {
    name: "Orange Tabby",
    body: "#d9772e",
    belly: "#f2c48a",
    eyes: "#27ae60",
    nose: "#e88b9a",
    pattern: "stripes",
    patternColor: "#ba4a00",
    points: null
  },
  siamese: {
    name: "Siamese",
    body: "#f4ece1",
    belly: "#fdfefe",
    eyes: "#3498db",
    nose: "#5a4536",
    pattern: "siamese_points",
    patternColor: "#4a3728",
    points: "#4a3728"
  },
  calico: {
    name: "Calico Cat",
    body: "#ffffff",
    belly: "#ffffff",
    eyes: "#f39c12",
    nose: "#f88888",
    pattern: "calico_patches",
    patternColor: "#d9772e",
    points: "#2c3e50"
  },
  mackerel: {
    name: "Mackerel Tabby",
    body: "#7f8c8d",
    belly: "#ecf0f1",
    eyes: "#2ecc71",
    nose: "#e88b9a",
    pattern: "stripes",
    patternColor: "#2c3e50",
    points: null
  }
};

// -----------------------------------------------------------------------------
// 2. Web Audio Synthesizer (Zero audio files needed, 100% synthesized)
// -----------------------------------------------------------------------------
class SoundSynth {
  constructor() {
    this.ctx = null;
    this.enabled = true;
  }

  _initContext() {
    if (!this.ctx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        this.ctx = new AudioContextClass();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  playPurr() {
    if (!this.enabled) return;
    this._initContext();
    if (!this.ctx) return;

    try {
      const sampleRate = 22050;
      const duration = 1.2;
      const buffer = this.ctx.createBuffer(1, sampleRate * duration, sampleRate);
      const data = buffer.getChannelData(0);

      // Low frequency rumble (~28 Hz) modulated by 3 Hz breathing envelope + harmonics
      for (let i = 0; i < data.length; i++) {
        const t = i / sampleRate;
        let val = Math.sin(2 * Math.PI * 28 * t);
        const env = 0.5 + 0.5 * Math.sin(2 * Math.PI * 3 * t);
        val += 0.3 * Math.sin(2 * Math.PI * 56 * t) * env;
        val += 0.1 * Math.sin(2 * Math.PI * 84 * t) * env;
        data[i] = val * env * 0.45;
      }

      const source = this.ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(this.ctx.destination);
      source.start();
    } catch (e) {
      console.warn("Purr synthesis failed:", e);
    }
  }

  playMeow() {
    if (!this.enabled) return;
    this._initContext();
    if (!this.ctx) return;

    try {
      const sampleRate = 22050;
      const duration = 0.42;
      const buffer = this.ctx.createBuffer(1, sampleRate * duration, sampleRate);
      const data = buffer.getChannelData(0);

      // Frequency sweep from 450 Hz -> 800 Hz -> 550 Hz
      for (let i = 0; i < data.length; i++) {
        const t = i / sampleRate;
        let freq;
        if (t < 0.16) {
          freq = 450 + (350 * (t / 0.16));
        } else {
          freq = 800 - (250 * ((t - 0.16) / 0.26));
        }
        let val = Math.sin(2 * Math.PI * freq * t);
        val += 0.4 * Math.sin(2 * Math.PI * (freq * 2) * t);
        val += 0.2 * Math.sin(2 * Math.PI * (freq * 3) * t);

        let env = 1.0;
        if (t < 0.04) {
          env = t / 0.04;
        } else if (t > 0.32) {
          env = Math.max(0, 1.0 - ((t - 0.32) / 0.1));
        }
        data[i] = val * env * 0.38;
      }

      const source = this.ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(this.ctx.destination);
      source.start();
    } catch (e) {
      console.warn("Meow synthesis failed:", e);
    }
  }
}

// -----------------------------------------------------------------------------
// 3. Kitty Procedural Vector Renderer
// -----------------------------------------------------------------------------
class KittyCanvasEngine {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.synth = options.synth || new SoundSynth();

    // Scale & Position
    this.scale = 1.15;
    this.cx = this.canvas.width / 2;
    this.cy = this.canvas.height / 2 + 10;

    // Skin & State
    this.currentSkinKey = "black";
    this.skin = COAT_SKINS.black;
    this.isDragging = false;
    this.wobbleAngle = 0;
    this.dragOffsetX = 0;
    this.dragOffsetY = 0;

    // Eye tracking & Blinking
    this.cursorX = window.innerWidth / 2;
    this.cursorY = window.innerHeight / 2;
    this.pupilDx = 0;
    this.pupilDy = 0;
    this.isBlinking = false;
    this.blinkEndTime = 0;
    this.nextBlinkTime = performance.now() + 2500;

    // Interactions
    this.lastClickTime = 0;
    this.hearts = [];

    // Hardware Telemetry Simulation / Browser API
    this.telemetry = {
      cpu: 18,
      ram: 5.6,
      gpu: 22,
      battery: 92,
      isCharging: true
    };
    this._initBatteryMonitor();

    // Bind event listeners
    this._initEvents();

    // Start render loop
    this.render = this.render.bind(this);
    requestAnimationFrame(this.render);
  }

  setSkin(skinKey) {
    if (COAT_SKINS[skinKey]) {
      this.currentSkinKey = skinKey;
      this.skin = COAT_SKINS[skinKey];
      const label = document.getElementById('activeBreedLabel');
      if (label) label.textContent = this.skin.name;
    }
  }

  _initBatteryMonitor() {
    if (navigator.getBattery) {
      navigator.getBattery().then(bat => {
        this.telemetry.battery = Math.round(bat.level * 100);
        this.telemetry.isCharging = bat.charging;
        bat.addEventListener('levelchange', () => {
          this.telemetry.battery = Math.round(bat.level * 100);
        });
        bat.addEventListener('chargingchange', () => {
          this.telemetry.isCharging = bat.charging;
        });
      }).catch(() => {});
    }
  }

  _initEvents() {
    // Global mouse tracking for pupil movement
    window.addEventListener('mousemove', (e) => {
      this.cursorX = e.clientX;
      this.cursorY = e.clientY;
    });

    // Drag-and-drop on canvas
    const anchor = document.getElementById('kittyAnchor');
    const stage = document.getElementById('stageArea');

    const onPointerDown = (e) => {
      this.synth._initContext();
      this.isDragging = true;
      const rect = anchor.getBoundingClientRect();
      this.dragOffsetX = (e.clientX || (e.touches && e.touches[0].clientX)) - rect.left;
      this.dragOffsetY = (e.clientY || (e.touches && e.touches[0].clientY)) - rect.top;

      const hints = document.getElementById('stageHints');
      if (hints) hints.style.opacity = '0';
    };

    const onPointerMove = (e) => {
      if (!this.isDragging) return;
      const clientX = e.clientX || (e.touches && e.touches[0].clientX);
      const clientY = e.clientY || (e.touches && e.touches[0].clientY);

      // If floating companion mode
      if (document.body.classList.contains('mode-floating-companion')) {
        anchor.style.left = `${clientX - this.dragOffsetX}px`;
        anchor.style.top = `${clientY - this.dragOffsetY}px`;
        anchor.style.right = 'auto';
        anchor.style.bottom = 'auto';
      } else if (stage) {
        const stageRect = stage.getBoundingClientRect();
        const newX = clientX - stageRect.left - this.dragOffsetX;
        const newY = clientY - stageRect.top - this.dragOffsetY;
        anchor.style.position = 'absolute';
        anchor.style.left = `${Math.max(10, Math.min(stageRect.width - 200, newX))}px`;
        anchor.style.top = `${Math.max(10, Math.min(stageRect.height - 200, newY))}px`;
      }
    };

    const onPointerUp = (e) => {
      if (!this.isDragging) return;
      this.isDragging = false;
      this.wobbleAngle = 0;
    };

    anchor.addEventListener('mousedown', onPointerDown);
    window.addEventListener('mousemove', onPointerMove);
    window.addEventListener('mouseup', onPointerUp);

    anchor.addEventListener('touchstart', onPointerDown, { passive: true });
    window.addEventListener('touchmove', onPointerMove, { passive: true });
    window.addEventListener('touchend', onPointerUp);

    // Click handler: 1st Click = System Status, 2nd Click / rapid = Meow Chat
    anchor.addEventListener('click', (e) => {
      const now = performance.now();
      const bubble = document.getElementById('speechBubble');
      const chat = document.getElementById('chatWindow');

      this.spawnHearts();
      this.synth.playPurr();

      if (bubble.style.display !== 'none' || (now - this.lastClickTime < 3500 && chat.style.display === 'none')) {
        // 2nd Click -> Open Meow Chat!
        bubble.style.display = 'none';
        chat.style.display = 'flex';
        this.synth.playMeow();
        this.lastClickTime = 0;
      } else {
        // 1st Click -> Show System Status Card
        this.updateSystemStatus();
        bubble.style.display = 'block';
        this.lastClickTime = now;
      }
    });
  }

  updateSystemStatus() {
    // Dynamic slight fluctuations for realistic HUD simulation
    this.telemetry.cpu = Math.floor(14 + Math.random() * 18);
    this.telemetry.ram = (4.8 + Math.random() * 1.6).toFixed(1);
    this.telemetry.gpu = Math.floor(18 + Math.random() * 20);

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    document.getElementById('statusClock').textContent = timeStr;
    document.getElementById('statCpu').textContent = `${this.telemetry.cpu}%`;
    document.getElementById('statCpuBar').style.width = `${this.telemetry.cpu}%`;

    document.getElementById('statRam').textContent = `${this.telemetry.ram} GB`;
    document.getElementById('statRamBar').style.width = `${Math.round((this.telemetry.ram / 16) * 100)}%`;

    document.getElementById('statGpu').textContent = `${this.telemetry.gpu}%`;
    document.getElementById('statGpuBar').style.width = `${this.telemetry.gpu}%`;

    const batIcon = this.telemetry.isCharging ? '⚡' : '';
    document.getElementById('statBat').textContent = `${this.telemetry.battery}% ${batIcon}`;
    document.getElementById('statBatBar').style.width = `${this.telemetry.battery}%`;
  }

  spawnHearts() {
    for (let i = 0; i < 4; i++) {
      this.hearts.push({
        x: (Math.random() - 0.5) * 50,
        y: -30 + (Math.random() - 0.5) * 20,
        size: 7 + Math.random() * 5,
        opacity: 1.0,
        vy: -0.8 - Math.random() * 0.8
      });
    }
  }

  // --- Exact Mathematical Fur Blob from pet_window.py ---
  drawFurBlob(cx, cy, rx, ry, fill, tuftLen = 5, n = 22, phase = 0) {
    const ctx = this.ctx;
    ctx.save();
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
      const a = phase + (i / n) * 2 * Math.PI;
      const bx = cx + Math.cos(a) * rx;
      const by = cy + Math.sin(a) * ry;
      if (i === 0) {
        ctx.moveTo(bx, by);
      } else {
        const am = a - (Math.PI / n);
        const tx = cx + Math.cos(am) * (rx + tuftLen);
        const ty = cy + Math.sin(am) * (ry + tuftLen);
        ctx.lineTo(tx, ty);
        ctx.lineTo(bx, by);
      }
    }
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.restore();
  }

  // Darken a hex color
  _darken(hex, factor = 0.7) {
    if (hex.startsWith('#')) hex = hex.slice(1);
    let num = parseInt(hex, 16);
    let r = Math.floor(((num >> 16) & 255) * factor);
    let g = Math.floor(((num >> 8) & 255) * factor);
    let b = Math.floor((num & 255) * factor);
    return `rgb(${r}, ${g}, ${b})`;
  }

  render(timestamp) {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // Blinking logic (80ms quick natural blink)
    if (timestamp > this.nextBlinkTime) {
      this.isBlinking = true;
      this.blinkEndTime = timestamp + 90;
      this.nextBlinkTime = timestamp + 3000 + Math.random() * 3500;
    }
    if (this.isBlinking && timestamp > this.blinkEndTime) {
      this.isBlinking = false;
    }

    // Cursor tracking calculation
    const rect = this.canvas.getBoundingClientRect();
    const kittyScreenX = rect.left + this.cx;
    const kittyScreenY = rect.top + this.cy - 18;
    const dx = this.cursorX - kittyScreenX;
    const dy = this.cursorY - kittyScreenY;
    const dist = Math.hypot(dx, dy);

    if (dist > 2.0 && !this.isBlinking) {
      this.pupilDx = Math.max(-3.0, Math.min(3.0, (dx / dist) * 3.0));
      this.pupilDy = Math.max(-2.5, Math.min(2.5, (dy / dist) * 2.5));
    } else {
      this.pupilDx = 0;
      this.pupilDy = 0;
    }

    // Dragging physics
    let scaleX = 1.0;
    let scaleY = 1.0;
    let cyLift = 0;
    if (this.isDragging) {
      scaleX = 0.88;
      scaleY = 1.25;
      cyLift = -6;
      this.wobbleAngle = Math.sin(timestamp * 0.015) * 0.08;
    }

    // Palette
    const fur = this.skin.body;
    const furDark = this._darken(fur, 0.65);
    const furLight = this.skin.belly;
    const amber = this.skin.eyes;
    const amberDark = this._darken(amber, 0.72);
    const noseColor = this.skin.nose;
    const pattern = this.skin.pattern;
    const patColor = this.skin.patternColor;
    const pointsColor = this.skin.points;

    ctx.save();
    ctx.translate(this.cx, this.cy + cyLift);
    if (this.isDragging && this.wobbleAngle !== 0) {
      ctx.rotate(this.wobbleAngle);
    }
    ctx.scale(this.scale * scaleX, this.scale * scaleY);

    // 1. Ground Shadow
    if (!this.isDragging) {
      ctx.save();
      ctx.beginPath();
      ctx.ellipse(0, 48, 30, 6.5, 0, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(0, 0, 0, 0.28)";
      ctx.fill();
      ctx.restore();
    }

    // 2. Fluffy Bushy Tail (Curled calm static silhouette)
    const tailFur = (pattern === "siamese_points" && pointsColor) ? pointsColor : fur;
    let tailPts = [
      { x: 26, y: 34, r: 12 },
      { x: 40, y: 26, r: 13 },
      { x: 46, y: 8,  r: 12 },
      { x: 42, y: -8, r: 10 },
      { x: 34, y: -18, r: 7 }
    ];
    if (this.isDragging) {
      tailPts = [
        { x: 20, y: 40, r: 11 },
        { x: 30, y: 30, r: 12 },
        { x: 34, y: 16, r: 12 },
        { x: 30, y: 4,  r: 10 }
      ];
    }
    for (let p of tailPts) {
      this.drawFurBlob(p.x, p.y, p.r, p.r, furDark, 4, 14);
    }
    for (let p of tailPts) {
      this.drawFurBlob(p.x, p.y, p.r - 2, p.r - 2, tailFur, 3, 12);
    }
    if (pattern === "stripes") {
      ctx.save();
      ctx.strokeStyle = patColor;
      ctx.lineWidth = 2.4;
      ctx.lineCap = "round";
      for (let p of tailPts.slice(1, 4)) {
        ctx.beginPath();
        ctx.moveTo(p.x - 4, p.y - 2);
        ctx.lineTo(p.x + 4, p.y + 2);
        ctx.stroke();
      }
      ctx.restore();
    }

    // 3. Spiky Fluffy Ears
    const earFur = (pattern === "siamese_points" && pointsColor) ? pointsColor : fur;
    const ears = this.isDragging ? [{ x: -20, y: -34 }, { x: 20, y: -34 }] : [{ x: -19, y: -42 }, { x: 19, y: -42 }];
    const earInner = this._darken(noseColor, 0.85);

    for (let e of ears) {
      this.drawFurBlob(e.x, e.y, 12, 15, furDark, 5, 12);
      this.drawFurBlob(e.x, e.y, 9, 12, earFur, 4, 11);
      ctx.save();
      ctx.beginPath();
      ctx.ellipse(e.x - (e.x > 0 ? 3.5 : -3.5), e.y - 4, 3.5, 5.5, 0, 0, Math.PI * 2);
      ctx.fillStyle = earInner;
      ctx.fill();
      ctx.restore();
    }

    // 4. Fluffy Body
    this.drawFurBlob(0, 22, 30, 26, furDark, 6, 26);
    this.drawFurBlob(0, 22, 27, 23, fur, 5, 24);

    // Calico body patches
    if (pattern === "calico_patches") {
      ctx.save();
      ctx.beginPath();
      ctx.ellipse(-20, 10, 9, 8, 0, 0, Math.PI * 2);
      ctx.fillStyle = patColor;
      ctx.fill();
      if (pointsColor) {
        ctx.beginPath();
        ctx.ellipse(4, 20, 9, 7.5, 0, 0, Math.PI * 2);
        ctx.fillStyle = pointsColor;
        ctx.fill();
      }
      ctx.restore();
    }

    // Chest sheen
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(0, 24, 11, 13, 0, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
    ctx.fill();
    ctx.restore();

    // Tabby body stripes
    if (pattern === "stripes") {
      ctx.save();
      ctx.strokeStyle = patColor;
      ctx.lineWidth = 2.2;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.arc(-14, 18, 7, 0.4, 2.0);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(-14, 26, 7, 0.4, 2.0);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(14, 18, 7, 1.1, 2.7);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(14, 26, 7, 1.1, 2.7);
      ctx.stroke();
      ctx.restore();
    }

    // 5. Fluffy Head
    this.drawFurBlob(0, -18, 33, 30, furDark, 6, 30, 0.15);
    this.drawFurBlob(0, -18, 30, 27, fur, 5, 28, 0.15);

    // Siamese mask
    if (pattern === "siamese_points" && pointsColor) {
      ctx.save();
      ctx.beginPath();
      ctx.ellipse(0, -25, 18, 13, 0, 0, Math.PI * 2);
      ctx.fillStyle = pointsColor;
      ctx.globalAlpha = 0.92;
      ctx.fill();
      ctx.restore();
    }

    // Calico head patch
    if (pattern === "calico_patches") {
      ctx.save();
      ctx.beginPath();
      ctx.ellipse(10, -32, 9, 8, 0, 0, Math.PI * 2);
      ctx.fillStyle = patColor;
      ctx.fill();
      ctx.restore();
    }

    // Tabby forehead "M"
    if (pattern === "stripes") {
      ctx.save();
      ctx.strokeStyle = patColor;
      ctx.lineWidth = 2.0;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(-7, -29);
      ctx.lineTo(-3.5, -22);
      ctx.lineTo(0, -26);
      ctx.lineTo(3.5, -22);
      ctx.lineTo(7, -29);
      ctx.stroke();
      ctx.restore();
    }

    // 6. Blush Cheeks
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(-20, -12, 7.5, 4.5, 0, 0, Math.PI * 2);
    ctx.ellipse(20, -12, 7.5, 4.5, 0, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 130, 140, 0.28)";
    ctx.fill();
    ctx.restore();

    // 7. Eyes (Awake, amber sclera, slit pupil following cursor, grumpy eyelids)
    const eyeCentres = [{ x: -12, y: -20 }, { x: 12, y: -20 }];
    const erX = 10.0;
    const erY = 11.0;

    if (this.isBlinking) {
      ctx.save();
      ctx.strokeStyle = furDark;
      ctx.lineWidth = 2.6;
      ctx.lineCap = "round";
      for (let ec of eyeCentres) {
        ctx.beginPath();
        ctx.moveTo(ec.x - 8, ec.y - 1);
        ctx.quadraticCurveTo(ec.x, ec.y + 4, ec.x + 8, ec.y - 1);
        ctx.stroke();
      }
      ctx.restore();
    } else {
      for (let ec of eyeCentres) {
        const innerSign = ec.x < 0 ? 1 : -1;

        // Amber sclera outer & inner
        ctx.save();
        ctx.beginPath();
        ctx.ellipse(ec.x, ec.y, erX, erY, 0, 0, Math.PI * 2);
        ctx.fillStyle = amberDark;
        ctx.fill();

        ctx.beginPath();
        ctx.ellipse(ec.x + 0.8, ec.y + 0.8, erX - 1.5, erY - 1.5, 0, 0, Math.PI * 2);
        ctx.fillStyle = amber;
        ctx.fill();

        // Slit pupil
        ctx.beginPath();
        ctx.ellipse(ec.x + this.pupilDx, ec.y + this.pupilDy, 2.4, 7.5, 0, 0, Math.PI * 2);
        ctx.fillStyle = "#14140f";
        ctx.fill();

        // Gloss highlight
        ctx.beginPath();
        ctx.ellipse(ec.x - 3 + this.pupilDx, ec.y - 5 + this.pupilDy, 1.8, 1.8, 0, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 255, 255, 0.85)";
        ctx.fill();

        // Grumpy stylized upper lid
        if (!this.isDragging) {
          const innerX = ec.x + innerSign * (erX + 1.5);
          const outerX = ec.x - innerSign * (erX + 1.5);
          ctx.beginPath();
          ctx.moveTo(outerX, ec.y - erY - 2);
          ctx.lineTo(innerX, ec.y - erY - 2);
          ctx.lineTo(innerX, ec.y + 1);
          ctx.lineTo(outerX, ec.y - erY + 4);
          ctx.closePath();
          ctx.fillStyle = fur;
          ctx.fill();

          // Brow tuft
          ctx.beginPath();
          ctx.moveTo(outerX, ec.y - erY - 1);
          ctx.lineTo(innerX, ec.y - erY - 4);
          ctx.lineTo(innerX, ec.y - erY + 1);
          ctx.closePath();
          ctx.fillStyle = furDark;
          ctx.fill();
        }
        ctx.restore();
      }
    }

    // 8. Nose
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(-4, -6);
    ctx.lineTo(4, -6);
    ctx.lineTo(0, -1);
    ctx.closePath();
    ctx.fillStyle = noseColor;
    ctx.fill();
    ctx.restore();

    // 9. Downturned :3 Mouth & Little White Fang
    ctx.save();
    ctx.strokeStyle = furDark;
    ctx.lineWidth = 1.8;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(0, -1);
    ctx.quadraticCurveTo(-5, 3, -10, 0);
    ctx.moveTo(0, -1);
    ctx.quadraticCurveTo(5, 3, 10, 0);
    ctx.stroke();

    // Tiny white fang
    ctx.beginPath();
    ctx.moveTo(-6, 1);
    ctx.lineTo(-2.5, 1);
    ctx.lineTo(-4, 6);
    ctx.closePath();
    ctx.fillStyle = "#fffdf5";
    ctx.fill();
    ctx.restore();

    // 10. Whiskers (3 on each side)
    ctx.save();
    ctx.strokeStyle = "rgba(230, 230, 230, 0.65)";
    ctx.lineWidth = 1.3;
    for (let sign of [-1, 1]) {
      ctx.beginPath();
      ctx.moveTo(sign * 10, -8);
      ctx.lineTo(sign * 34, -12);
      ctx.moveTo(sign * 10, -5);
      ctx.lineTo(sign * 36, -5);
      ctx.moveTo(sign * 10, -2);
      ctx.lineTo(sign * 34, 3);
      ctx.stroke();
    }
    ctx.restore();

    // 11. Front Paws / Scruff Dangle
    let pawColor = (pattern === "siamese_points" && pointsColor) ? pointsColor : fur;
    if (this.isDragging) {
      // Scruff dangle limbs
      ctx.save();
      for (let sign of [-1, 1]) {
        this.drawFurBlob(sign * 18, 42, 6, 10, furDark, 3, 10);
        this.drawFurBlob(sign * 18, 42, 4.5, 8.5, pawColor, 2, 8);
      }
      ctx.restore();
    } else {
      // Resting cute paws
      ctx.save();
      for (let sign of [-1, 1]) {
        this.drawFurBlob(sign * 14, 40, 8, 7, furDark, 3, 12);
        this.drawFurBlob(sign * 14, 40, 6.5, 5.5, pawColor, 2, 10);
      }
      ctx.restore();
    }

    // 12. Floating Hearts
    if (this.hearts.length > 0) {
      for (let i = this.hearts.length - 1; i >= 0; i--) {
        const h = this.hearts[i];
        h.y += h.vy;
        h.opacity -= 0.015;
        if (h.opacity <= 0) {
          this.hearts.splice(i, 1);
        } else {
          ctx.save();
          ctx.font = `${Math.round(h.size)}px sans-serif`;
          ctx.fillStyle = `rgba(255, 75, 110, ${h.opacity})`;
          ctx.textAlign = 'center';
          ctx.fillText("❤️", h.x, h.y);
          ctx.restore();
        }
      }
    }

    ctx.restore();

    requestAnimationFrame(this.render);
  }
}

// -----------------------------------------------------------------------------
// 4. Page UI Controls & Chat Dialog Manager
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('kittyCanvas');
  const synth = new SoundSynth();
  const kitty = new KittyCanvasEngine(canvas, { synth });

  // Skin Selector
  const skinButtons = document.querySelectorAll('.skin-btn');
  skinButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      skinButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const skin = btn.getAttribute('data-skin');
      kitty.setSkin(skin);
      synth.playMeow();
    });
  });

  // Action Buttons
  document.getElementById('btnPetKitty').addEventListener('click', () => {
    kitty.spawnHearts();
    synth.playPurr();
  });

  document.getElementById('btnInspectHud').addEventListener('click', () => {
    kitty.updateSystemStatus();
    const bubble = document.getElementById('speechBubble');
    bubble.style.display = bubble.style.display === 'none' ? 'block' : 'none';
    synth.playPurr();
  });

  document.getElementById('btnToggleChat').addEventListener('click', () => {
    const chat = document.getElementById('chatWindow');
    chat.style.display = chat.style.display === 'none' ? 'flex' : 'none';
    synth.playMeow();
  });

  // Toggle Sound Button
  const btnToggleSound = document.getElementById('btnToggleSound');
  btnToggleSound.addEventListener('click', () => {
    synth.enabled = !synth.enabled;
    btnToggleSound.textContent = synth.enabled ? '🔊' : '🔇';
  });

  // Float on Screen Companion Mode Toggle
  const btnFloatMode = document.getElementById('btnFloatMode');
  btnFloatMode.addEventListener('click', () => {
    const isFloating = document.body.classList.toggle('mode-floating-companion');
    btnFloatMode.textContent = isFloating ? '📍 Dock to Stage' : '🪟 Float on Screen';
  });

  // Chat Close Button
  document.getElementById('btnCloseChat').addEventListener('click', () => {
    document.getElementById('chatWindow').style.display = 'none';
  });

  // Chat Responses Engine
  const chatMessages = document.getElementById('chatMessages');
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');

  const addChatMessage = (text, sender = 'user') => {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg msg-${sender}`;
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'msg-bubble';
    bubbleDiv.textContent = text;
    msgDiv.appendChild(bubbleDiv);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  };

  const generateCatReply = (query) => {
    const q = query.toLowerCase();
    if (q.includes('joke')) {
      const jokes = [
        "Why was the cat sitting on the computer? To keep an eye on the mouse! 😹",
        "What do you call a pile of kittens? A meowntain! 🏔️",
        "What is a cat's favorite color? Purr-ple! 💜",
        "What did the cat say when it broke the vase? It was an undocumented feature, meow! 😼"
      ];
      return jokes[Math.floor(Math.random() * jokes.length)];
    }
    if (q.includes('purr')) {
      synth.playPurr();
      return "Purrrrrrrrr... 🎶 Soft vibrations activated! You are an awesome human!";
    }
    if (q.includes('desktop') || q.includes('run') || q.includes('install')) {
      return "To run me right on your actual computer screen: clone the repo and double-click `run.bat` on Windows! I'll sit borderless on top of your windows!";
    }
    if (q.includes('who are you') || q.includes('what can you do')) {
      return "I'm Kitty AI! I am a smart desktop companion built with Python and PyQt6. I track your mouse, monitor CPU/RAM/GPU, chat with Google Gemini, and keep you focused!";
    }
    if (q.includes('pomodoro') || q.includes('focus')) {
      return "Focus time! Paws down and get to work! I'll keep your PC running cool while you code! 🐾";
    }

    const defaultReplies = [
      "Meow! That's interesting! Tell me more human! 🐾",
      "Mrrrow? I was just checking your CPU temperatures. Everything looks cozy!",
      "Headbutts your hand gently. 🐱 I'm always here while you work!",
      "Meow meow! Have you tested switching my coat to Orange Tabby or Siamese yet?"
    ];
    return defaultReplies[Math.floor(Math.random() * defaultReplies.length)];
  };

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    addChatMessage(text, 'user');
    chatInput.value = '';

    setTimeout(() => {
      const reply = generateCatReply(text);
      addChatMessage(reply, 'kitty');
      synth.playMeow();
    }, 450);
  });

  // Quick suggestion chips
  document.querySelectorAll('.chip-suggestion').forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      addChatMessage(prompt, 'user');
      setTimeout(() => {
        const reply = generateCatReply(prompt);
        addChatMessage(reply, 'kitty');
        synth.playMeow();
      }, 400);
    });
  });

  // Copy commands button
  const btnCopyCommands = document.getElementById('btnCopyCommands');
  if (btnCopyCommands) {
    btnCopyCommands.addEventListener('click', () => {
      const text = `git clone https://github.com/HarshBhayani77/kitty.git\ncd kitty\n.\\run.bat`;
      navigator.clipboard.writeText(text).then(() => {
        btnCopyCommands.textContent = '✓ Copied!';
        setTimeout(() => { btnCopyCommands.textContent = '📋 Copy'; }, 2000);
      });
    });
  }
});
