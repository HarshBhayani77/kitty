/**
 * Kitty — Procedural Vector Canvas Engine & Companion Simulator
 * Replicates the PyQt6 QPainter rendering from KittyAI/ui/pet_window.py 1:1 in Web Canvas.
 */

// -----------------------------------------------------------------------------
// 1. Breed / Coat Color Definitions
// -----------------------------------------------------------------------------
const COAT_SKINS = {
  black: {
    name: "Midnight Black",
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
    name: "Calico",
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
// 2. Web Audio Synthesizer (Zero external audio files needed)
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
        data[i] = val * env * 0.42;
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
      const duration = 0.4;
      const buffer = this.ctx.createBuffer(1, sampleRate * duration, sampleRate);
      const data = buffer.getChannelData(0);

      // Frequency sweep from 450 Hz -> 800 Hz -> 550 Hz
      for (let i = 0; i < data.length; i++) {
        const t = i / sampleRate;
        let freq;
        if (t < 0.16) {
          freq = 450 + (350 * (t / 0.16));
        } else {
          freq = 800 - (250 * ((t - 0.16) / 0.24));
        }
        let val = Math.sin(2 * Math.PI * freq * t);
        val += 0.4 * Math.sin(2 * Math.PI * (freq * 2) * t);
        val += 0.2 * Math.sin(2 * Math.PI * (freq * 3) * t);

        let env = 1.0;
        if (t < 0.04) {
          env = t / 0.04;
        } else if (t > 0.3) {
          env = Math.max(0, 1.0 - ((t - 0.3) / 0.1));
        }
        data[i] = val * env * 0.35;
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
    // Mouse tracking for pupil movement
    window.addEventListener('mousemove', (e) => {
      this.cursorX = e.clientX;
      this.cursorY = e.clientY;
    });

    const anchor = document.getElementById('kittyAnchor');
    const stage = document.getElementById('stageArea');
    const bubble = document.getElementById('speechBubble');
    const chat = document.getElementById('chatWindow');

    // Prevent clicks inside telemetry bubble or chat window from bubbling up to Kitty
    if (bubble) {
      bubble.addEventListener('click', (e) => e.stopPropagation());
      bubble.addEventListener('mousedown', (e) => e.stopPropagation());
    }
    if (chat) {
      chat.addEventListener('click', (e) => e.stopPropagation());
      chat.addEventListener('mousedown', (e) => e.stopPropagation());
    }

    // Drag-and-drop state on canvas
    this.isPointerDown = false;
    this.hasMoved = false;
    this.startClientX = 0;
    this.startClientY = 0;

    const onPointerDown = (e) => {
      this.synth._initContext();
      this.isPointerDown = true;
      this.hasMoved = false;

      const clientX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
      const clientY = e.clientY || (e.touches && e.touches[0].clientY) || 0;
      this.startClientX = clientX;
      this.startClientY = clientY;

      const rect = anchor.getBoundingClientRect();
      this.dragOffsetX = clientX - rect.left;
      this.dragOffsetY = clientY - rect.top;

      const hints = document.getElementById('stageHints');
      if (hints) hints.style.opacity = '0';
    };

    const onPointerMove = (e) => {
      if (!this.isPointerDown) return;
      const clientX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
      const clientY = e.clientY || (e.touches && e.touches[0].clientY) || 0;

      const dist = Math.hypot(clientX - this.startClientX, clientY - this.startClientY);
      if (dist > 6) {
        this.hasMoved = true;
        this.isDragging = true;
      }

      if (!this.isDragging) return;

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

    const onPointerUp = () => {
      this.isPointerDown = false;
      this.isDragging = false;
      this.wobbleAngle = 0;
    };

    this.canvas.addEventListener('mousedown', onPointerDown);
    window.addEventListener('mousemove', onPointerMove);
    window.addEventListener('mouseup', onPointerUp);

    this.canvas.addEventListener('touchstart', onPointerDown, { passive: true });
    window.addEventListener('touchmove', onPointerMove, { passive: true });
    window.addEventListener('touchend', onPointerUp);

    // Click on Kitty Canvas ONLY (not whole anchor container)
    this.canvas.addEventListener('click', (e) => {
      // If user was dragging, do NOT trigger click action
      if (this.hasMoved) {
        this.hasMoved = false;
        return;
      }

      this.spawnHearts();

      const bubbleEl = document.getElementById('speechBubble');
      const chatEl = document.getElementById('chatWindow');
      const isBubbleOpen = bubbleEl && bubbleEl.style.display !== 'none';
      const isChatOpen = chatEl && chatEl.style.display !== 'none';

      if (!isBubbleOpen && !isChatOpen) {
        // 1st click: Open Hardware HUD snapshot
        this.updateSystemStatus();
        if (bubbleEl) bubbleEl.style.display = 'block';
        this.synth.playPurr();
      } else if (isBubbleOpen && !isChatOpen) {
        // 2nd click: Transition from HUD to Console
        if (bubbleEl) bubbleEl.style.display = 'none';
        if (chatEl) chatEl.style.display = 'flex';
        this.synth.playMeow();
      } else {
        // Already interacting: pet kitty
        this.synth.playPurr();
      }
    });
  }

  updateSystemStatus() {
    this.telemetry.cpu = Math.floor(14 + Math.random() * 16);
    this.telemetry.ram = (4.8 + Math.random() * 1.4).toFixed(1);
    this.telemetry.gpu = Math.floor(18 + Math.random() * 18);

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const clock = document.getElementById('statusClock');
    if (clock) clock.textContent = timeStr;

    const statCpu = document.getElementById('statCpu');
    if (statCpu) statCpu.textContent = `${this.telemetry.cpu}%`;
    const statCpuBar = document.getElementById('statCpuBar');
    if (statCpuBar) statCpuBar.style.width = `${this.telemetry.cpu}%`;

    const statRam = document.getElementById('statRam');
    if (statRam) statRam.textContent = `${this.telemetry.ram} GB`;
    const statRamBar = document.getElementById('statRamBar');
    if (statRamBar) statRamBar.style.width = `${Math.round((this.telemetry.ram / 16) * 100)}%`;

    const statGpu = document.getElementById('statGpu');
    if (statGpu) statGpu.textContent = `${this.telemetry.gpu}%`;
    const statGpuBar = document.getElementById('statGpuBar');
    if (statGpuBar) statGpuBar.style.width = `${this.telemetry.gpu}%`;

    const statBat = document.getElementById('statBat');
    if (statBat) {
      const batIcon = this.telemetry.isCharging ? ' ⚡' : '';
      statBat.textContent = `${this.telemetry.battery}%${batIcon}`;
    }
    const statBatBar = document.getElementById('statBatBar');
    if (statBatBar) statBatBar.style.width = `${this.telemetry.battery}%`;
  }

  spawnHearts() {
    for (let i = 0; i < 3; i++) {
      this.hearts.push({
        x: (Math.random() - 0.5) * 44,
        y: -30 + (Math.random() - 0.5) * 16,
        size: 7 + Math.random() * 4,
        opacity: 0.9,
        vy: -0.7 - Math.random() * 0.7
      });
    }
  }

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
      this.blinkEndTime = timestamp + 85;
      this.nextBlinkTime = timestamp + 3200 + Math.random() * 3200;
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
      ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
      ctx.fill();
      ctx.restore();
    }

    // 2. Tail
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

    // 3. Fluffy Ears
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

    // 4. Body
    this.drawFurBlob(0, 22, 30, 26, furDark, 6, 26);
    this.drawFurBlob(0, 22, 27, 23, fur, 5, 24);

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

    ctx.save();
    ctx.beginPath();
    ctx.ellipse(0, 24, 11, 13, 0, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
    ctx.fill();
    ctx.restore();

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

    // 5. Head
    this.drawFurBlob(0, -18, 33, 30, furDark, 6, 30, 0.15);
    this.drawFurBlob(0, -18, 30, 27, fur, 5, 28, 0.15);

    if (pattern === "siamese_points" && pointsColor) {
      ctx.save();
      ctx.beginPath();
      ctx.ellipse(0, -25, 18, 13, 0, 0, Math.PI * 2);
      ctx.fillStyle = pointsColor;
      ctx.globalAlpha = 0.92;
      ctx.fill();
      ctx.restore();
    }

    if (pattern === "calico_patches") {
      ctx.save();
      ctx.beginPath();
      ctx.ellipse(10, -32, 9, 8, 0, 0, Math.PI * 2);
      ctx.fillStyle = patColor;
      ctx.fill();
      ctx.restore();
    }

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

    // 6. Subtle Cheeks
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(-20, -12, 7.5, 4.5, 0, 0, Math.PI * 2);
    ctx.ellipse(20, -12, 7.5, 4.5, 0, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 130, 140, 0.22)";
    ctx.fill();
    ctx.restore();

    // 7. Eyes
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

        ctx.save();
        ctx.beginPath();
        ctx.ellipse(ec.x, ec.y, erX, erY, 0, 0, Math.PI * 2);
        ctx.fillStyle = amberDark;
        ctx.fill();

        ctx.beginPath();
        ctx.ellipse(ec.x + 0.8, ec.y + 0.8, erX - 1.5, erY - 1.5, 0, 0, Math.PI * 2);
        ctx.fillStyle = amber;
        ctx.fill();

        ctx.beginPath();
        ctx.ellipse(ec.x + this.pupilDx, ec.y + this.pupilDy, 2.4, 7.5, 0, 0, Math.PI * 2);
        ctx.fillStyle = "#14140f";
        ctx.fill();

        ctx.beginPath();
        ctx.ellipse(ec.x - 3 + this.pupilDx, ec.y - 5 + this.pupilDy, 1.8, 1.8, 0, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 255, 255, 0.85)";
        ctx.fill();

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

    // 9. Mouth & Tiny White Fang
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

    ctx.beginPath();
    ctx.moveTo(-6, 1);
    ctx.lineTo(-2.5, 1);
    ctx.lineTo(-4, 6);
    ctx.closePath();
    ctx.fillStyle = "#fffdf5";
    ctx.fill();
    ctx.restore();

    // 10. Whiskers
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

    // 11. Paws / Scruff Dangle
    let pawColor = (pattern === "siamese_points" && pointsColor) ? pointsColor : fur;
    if (this.isDragging) {
      ctx.save();
      for (let sign of [-1, 1]) {
        this.drawFurBlob(sign * 18, 42, 6, 10, furDark, 3, 10);
        this.drawFurBlob(sign * 18, 42, 4.5, 8.5, pawColor, 2, 8);
      }
      ctx.restore();
    } else {
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
          ctx.fillStyle = `rgba(239, 68, 68, ${h.opacity})`;
          ctx.textAlign = 'center';
          ctx.fillText("♥", h.x, h.y);
          ctx.restore();
        }
      }
    }

    ctx.restore();

    requestAnimationFrame(this.render);
  }
}

// -----------------------------------------------------------------------------
// 4. Page UI Controls & Companion Dialogue Engine
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('kittyCanvas');
  const synth = new SoundSynth();
  const kitty = new KittyCanvasEngine(canvas, { synth });

  // Close buttons
  const btnCloseHud = document.getElementById('btnCloseHud');
  if (btnCloseHud) {
    btnCloseHud.addEventListener('click', (e) => {
      e.stopPropagation();
      const bubble = document.getElementById('speechBubble');
      if (bubble) bubble.style.display = 'none';
    });
  }

  const btnCloseChat = document.getElementById('btnCloseChat');
  if (btnCloseChat) {
    btnCloseChat.addEventListener('click', (e) => {
      e.stopPropagation();
      const chat = document.getElementById('chatWindow');
      if (chat) chat.style.display = 'none';
    });
  }

  // Coat selector buttons
  const coatButtons = document.querySelectorAll('.coat-btn, .skin-btn');
  coatButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      coatButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const skin = btn.getAttribute('data-skin');
      kitty.setSkin(skin);
      synth.playMeow();
    });
  });

  // Action Buttons
  const btnPet = document.getElementById('btnPetKitty');
  if (btnPet) {
    btnPet.addEventListener('click', (e) => {
      e.preventDefault();
      kitty.spawnHearts();
      synth.playPurr();
    });
  }

  const btnInspect = document.getElementById('btnInspectHud');
  if (btnInspect) {
    btnInspect.addEventListener('click', (e) => {
      e.preventDefault();
      const bubble = document.getElementById('speechBubble');
      if (bubble) {
        const isClosed = bubble.style.display === 'none' || !bubble.style.display;
        if (isClosed) {
          kitty.updateSystemStatus();
          bubble.style.display = 'block';
          synth.playPurr();
        } else {
          bubble.style.display = 'none';
        }
      }
    });
  }

  const btnChat = document.getElementById('btnToggleChat');
  if (btnChat) {
    btnChat.addEventListener('click', (e) => {
      e.preventDefault();
      const chat = document.getElementById('chatWindow');
      if (chat) {
        const isClosed = chat.style.display === 'none' || !chat.style.display;
        chat.style.display = isClosed ? 'flex' : 'none';
        if (isClosed) synth.playMeow();
      }
    });
  }

  // Audio Toggle
  const btnToggleSound = document.getElementById('btnToggleSound');
  const soundIcon = document.getElementById('soundIcon');
  if (btnToggleSound) {
    btnToggleSound.addEventListener('click', (e) => {
      e.preventDefault();
      synth.enabled = !synth.enabled;
      if (soundIcon) {
        soundIcon.textContent = synth.enabled ? 'Audio: ON' : 'Audio: OFF';
      }
    });
  }

  // Viewport Companion Mode Toggle
  const btnFloatMode = document.getElementById('btnFloatMode');
  const anchor = document.getElementById('kittyAnchor');
  if (btnFloatMode && anchor) {
    btnFloatMode.addEventListener('click', (e) => {
      e.preventDefault();
      const isFloating = document.body.classList.toggle('mode-floating-companion');
      btnFloatMode.textContent = isFloating ? 'Dock in Viewport' : 'Float in Viewport';
      // Reset inline styles so CSS takes over properly
      anchor.style.position = '';
      anchor.style.left = '';
      anchor.style.top = '';
      anchor.style.right = '';
      anchor.style.bottom = '';
    });
  }

  // Companion Console Dialogue
  const chatMessages = document.getElementById('chatMessages');
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');

  const addChatMessage = (text, sender = 'user') => {
    if (!chatMessages) return;
    const row = document.createElement('div');
    row.className = `console-row row-${sender === 'user' ? 'user' : 'companion'}`;
    const bubble = document.createElement('div');
    bubble.className = 'console-bubble';
    bubble.textContent = text;
    row.appendChild(bubble);
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  };

  const getCompanionResponse = (query) => {
    const q = query.toLowerCase();

    if (q.includes('launch') || q.includes('install') || q.includes('desktop') || q.includes('run')) {
      return "Desktop build: Run .\\run.bat on Windows or ./run.sh on Linux/macOS. Dependencies install automatically in an isolated venv.";
    }
    if (q.includes('status') || q.includes('diagnostic') || q.includes('hardware') || q.includes('cpu')) {
      kitty.updateSystemStatus();
      return `Telemetry: CPU at ${kitty.telemetry.cpu}%, RAM at ${kitty.telemetry.ram} GB, GPU at ${kitty.telemetry.gpu}%. Thermals nominal.`;
    }
    if (q.includes('feature') || q.includes('capability') || q.includes('what can you do')) {
      return "Core capabilities: Procedural vector avatar, non-blocking telemetry (psutil/GPUtil), Pomodoro focus timer, pinned desktop notes, and multi-model LLM chat.";
    }
    if (q.includes('audio') || q.includes('sound') || q.includes('purr')) {
      synth.playPurr();
      return "Synthesizing 28 Hz low-frequency sine rumble with 3 Hz amplitude modulation. Purr active.";
    }

    const defaultReplies = [
      "Query received. Background threads running without interruption.",
      "Acknowledged. Monitoring hardware state and system responsiveness.",
      "Meow. Telemetry poll updated. All parameters within safe limits.",
      "Standing by on the desktop viewport."
    ];
    return defaultReplies[Math.floor(Math.random() * defaultReplies.length)];
  };

  if (chatForm && chatInput) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (!text) return;

      addChatMessage(text, 'user');
      chatInput.value = '';

      setTimeout(() => {
        const reply = getCompanionResponse(text);
        addChatMessage(reply, 'companion');
        synth.playMeow();
      }, 350);
    });
  }

  // Preset chips (auto-open console if closed)
  document.querySelectorAll('.preset-chip, .chip-suggestion').forEach(chip => {
    chip.addEventListener('click', (e) => {
      e.preventDefault();
      const prompt = chip.getAttribute('data-prompt');
      if (!prompt) return;

      const chat = document.getElementById('chatWindow');
      if (chat && chat.style.display === 'none') {
        chat.style.display = 'flex';
      }

      addChatMessage(prompt, 'user');
      setTimeout(() => {
        const reply = getCompanionResponse(prompt);
        addChatMessage(reply, 'companion');
        synth.playMeow();
      }, 300);
    });
  });

  // Copy command button with fallback
  const btnCopyCommands = document.getElementById('btnCopyCommands');
  if (btnCopyCommands) {
    btnCopyCommands.addEventListener('click', (e) => {
      e.preventDefault();
      const text = `git clone https://github.com/HarshBhayani77/kitty.git\ncd kitty\n.\\run.bat`;
      
      const onCopied = () => {
        btnCopyCommands.textContent = '✓ Copied to Clipboard';
        setTimeout(() => { btnCopyCommands.textContent = 'Copy Instructions'; }, 2000);
      };

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(onCopied).catch(() => {
          fallbackCopy(text, onCopied);
        });
      } else {
        fallbackCopy(text, onCopied);
      }
    });
  }

  function fallbackCopy(text, callback) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      if (callback) callback();
    } catch (err) {}
    document.body.removeChild(ta);
  }
});
