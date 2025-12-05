/**
 * SPYDER - Dynamic Spider Web Animation System
 * Creates animated spider webs and crawling spiders across the webapp
 */

class SpiderWebSystem {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.webs = [];
        this.spiders = [];
        this.initialized = false;
    }

    init() {
        if (this.initialized) return;
        
        // Create canvas for web animations
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'spider-web-canvas';
        this.canvas.style.position = 'fixed';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '9999'; // High z-index to appear over content
        this.canvas.style.opacity = '1';
        
        document.body.prepend(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        // Create corner webs
        this.createCornerWebs();
        
        // Create crawling spiders (increased for visibility)
        this.createCrawlingSpiders(8);
        
        // Create hanging spiders (increased for visibility)
        this.createHangingSpiders(4);
        
        // Create fog particles
        this.createFogParticles(4);
        
        // Create floating ghosts (increased for visibility)
        this.createFloatingGhosts(5);
        
        // Create floating pumpkins
        this.createFloatingPumpkins(3);
        
        // Setup jump scare
        this.setupJumpScare();
        
        // Setup logo glitch animation
        this.setupLogoGlitch();
        
        // Start animation loop
        this.animate();
        
        this.initialized = true;
    }

    setupLogoGlitch() {
        const logoText = document.querySelector('.header h1');
        if (!logoText) return;
        
        let lastGlitchTime = Date.now();
        
        const animateGlitch = () => {
            const now = Date.now();
            const timeSinceLastGlitch = now - lastGlitchTime;
            
            // Trigger glitch every 8-12 seconds
            if (timeSinceLastGlitch > 8000 + Math.random() * 4000) {
                // Add glitch class
                logoText.classList.add('glitch-font');
                
                // Hold for 2 seconds
                setTimeout(() => {
                    // Remove glitch class
                    logoText.classList.remove('glitch-font');
                }, 2000);
                
                lastGlitchTime = now;
            }
            
            requestAnimationFrame(animateGlitch);
        };
        
        animateGlitch();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createCornerWebs() {
        const corners = [
            { x: 0, y: 0, anchor: 'top-left' },
            { x: window.innerWidth, y: 0, anchor: 'top-right' },
            { x: 0, y: window.innerHeight, anchor: 'bottom-left' },
            { x: window.innerWidth, y: window.innerHeight, anchor: 'bottom-right' }
        ];

        corners.forEach(corner => {
            this.webs.push(new SpiderWeb(corner.x, corner.y, corner.anchor));
        });

        // Reduced random webs for performance
        for (let i = 0; i < 2; i++) {
            const x = Math.random() * window.innerWidth;
            const y = Math.random() * window.innerHeight * 0.3; // Top third
            this.webs.push(new SpiderWeb(x, y, 'random'));
        }
    }

    createCrawlingSpiders(count) {
        for (let i = 0; i < count; i++) {
            const x = Math.random() * window.innerWidth;
            const y = Math.random() * window.innerHeight;
            this.spiders.push(new CrawlingSpider(x, y));
        }
    }

    createHangingSpiders(count) {
        this.hangingSpiders = [];
        for (let i = 0; i < count; i++) {
            const x = Math.random() * window.innerWidth;
            this.hangingSpiders.push(new HangingSpider(x));
        }
    }

    createFogParticles(count) {
        this.fogParticles = [];
        for (let i = 0; i < count; i++) {
            this.fogParticles.push(new FogParticle());
        }
    }

    createFloatingGhosts(count) {
        this.floatingGhosts = [];
        for (let i = 0; i < count; i++) {
            this.floatingGhosts.push(new FloatingGhost());
        }
    }

    createFloatingPumpkins(count) {
        this.floatingPumpkins = [];
        for (let i = 0; i < count; i++) {
            this.floatingPumpkins.push(new FloatingPumpkin());
        }
    }

    setupJumpScare() {
        // Jump scare every 30 seconds
        const scheduleJumpScare = () => {
            setTimeout(() => {
                this.triggerJumpScare();
                scheduleJumpScare();
            }, 30000); // 30 seconds
        };
        scheduleJumpScare();
    }

    triggerJumpScare() {
        // Start glitch effect 2 seconds BEFORE jump scare
        this.triggerGlitchEffect(2000);
        
        // Wait 2 seconds, then show jump scare
        setTimeout(() => {
            const random = Math.random();
            
            if (random < 0.5) {
                // 50% Ghost
                this.jumpScareGhost = new JumpScareGhost();
                setTimeout(() => {
                    this.jumpScareGhost = null;
                }, 2500);
            } else if (random < 0.8) {
                // 30% Pumpkin
                this.jumpscarePumpkin = new JumpScarePumpkin();
                setTimeout(() => {
                    this.jumpscarePumpkin = null;
                }, 2500);
            } else {
                // 20% Spider
                this.jumpScareSpider = new JumpScareSpider();
                setTimeout(() => {
                    this.jumpScareSpider = null;
                }, 2000);
            }
        }, 2000); // 2 second delay before creature appears
    }

    triggerGlitchEffect(delayBefore = 0) {
        const container = document.querySelector('.container');
        if (!container) return;
        
        // Start glitch after delay
        setTimeout(() => {
            container.classList.add('glitch-active');
            
            // Remove glitch after: 2s buffer + max creature duration (2.5s) + 2s buffer = 6.5s
            setTimeout(() => {
                container.classList.remove('glitch-active');
            }, 6500);
        }, delayBefore);
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw fog particles first (background layer)
        if (this.fogParticles) {
            this.fogParticles.forEach(fog => {
                fog.update();
                fog.draw(this.ctx);
            });
        }
        
        // Draw webs
        this.webs.forEach(web => web.draw(this.ctx));
        
        // Update and draw crawling spiders
        this.spiders.forEach(spider => {
            spider.update();
            spider.draw(this.ctx);
        });
        
        // Update and draw hanging spiders
        if (this.hangingSpiders) {
            this.hangingSpiders.forEach(spider => {
                spider.update();
                spider.draw(this.ctx);
            });
        }
        
        // Update and draw floating ghosts
        if (this.floatingGhosts) {
            this.floatingGhosts.forEach(ghost => {
                ghost.update();
                ghost.draw(this.ctx);
            });
        }
        
        // Update and draw floating pumpkins
        if (this.floatingPumpkins) {
            this.floatingPumpkins.forEach(pumpkin => {
                pumpkin.update();
                pumpkin.draw(this.ctx);
            });
        }
        
        // Draw jump scare spider (on top of everything)
        if (this.jumpScareSpider) {
            this.jumpScareSpider.update();
            this.jumpScareSpider.draw(this.ctx);
        }
        
        // Draw jump scare ghost (on top of everything)
        if (this.jumpScareGhost) {
            this.jumpScareGhost.update();
            this.jumpScareGhost.draw(this.ctx);
        }
        
        // Draw jump scare pumpkin (on top of everything)
        if (this.jumpscarePumpkin) {
            this.jumpscarePumpkin.update();
            this.jumpscarePumpkin.draw(this.ctx);
        }
        
        requestAnimationFrame(() => this.animate());
    }
}

class SpiderWeb {
    constructor(x, y, anchor) {
        this.x = x;
        this.y = y;
        this.anchor = anchor;
        this.strands = [];
        this.generateWeb();
    }

    generateWeb() {
        const size = 150 + Math.random() * 100;
        const rings = 5;
        const spokes = 6 + Math.floor(Math.random() * 4); // Random 6-9 spokes for asymmetry

        // Generate anchor points based on position
        let angleOffset = 0;
        let angleRange = Math.PI * 2;

        if (this.anchor === 'top-left') {
            angleOffset = 0;
            angleRange = Math.PI / 2;
        } else if (this.anchor === 'top-right') {
            angleOffset = Math.PI / 2;
            angleRange = Math.PI / 2;
        } else if (this.anchor === 'bottom-left') {
            angleOffset = Math.PI * 1.5;
            angleRange = Math.PI / 2;
        } else if (this.anchor === 'bottom-right') {
            angleOffset = Math.PI;
            angleRange = Math.PI / 2;
        }

        // Create ORGANIC spokes with random variations
        const spokeAngles = [];
        for (let i = 0; i < spokes; i++) {
            // Add random angle variation for organic feel
            const baseAngle = angleOffset + (i / spokes) * angleRange;
            const angleVariation = (Math.random() - 0.5) * 0.3; // Random offset
            spokeAngles.push(baseAngle + angleVariation);
        }

        // Create spokes with organic curves
        spokeAngles.forEach(angle => {
            const lengthVariation = 0.7 + Math.random() * 0.6; // Random length 70-130%
            const endX = this.x + Math.cos(angle) * size * lengthVariation;
            const endY = this.y + Math.sin(angle) * size * lengthVariation;
            
            // Add slight curve to spokes for organic feel
            const midX = this.x + Math.cos(angle) * size * lengthVariation * 0.5;
            const midY = this.y + Math.sin(angle) * size * lengthVariation * 0.5;
            const curveOffset = (Math.random() - 0.5) * 15;
            
            this.strands.push({
                type: 'spoke',
                x1: this.x,
                y1: this.y,
                x2: endX,
                y2: endY,
                midX: midX + curveOffset,
                midY: midY + curveOffset,
                opacity: 0.2 + Math.random() * 0.3,
                curved: true
            });
        });

        // Create IRREGULAR rings with organic distortion
        for (let ring = 1; ring <= rings; ring++) {
            const ringSize = (size / rings) * ring;
            const points = [];
            
            spokeAngles.forEach(angle => {
                // Add random distortion to each ring point
                const distortion = 0.85 + Math.random() * 0.3; // 85-115% of ring size
                const angleJitter = (Math.random() - 0.5) * 0.2;
                const finalAngle = angle + angleJitter;
                
                points.push({
                    x: this.x + Math.cos(finalAngle) * ringSize * distortion,
                    y: this.y + Math.sin(finalAngle) * ringSize * distortion
                });
            });
            
            // Connect ring points with organic curves
            for (let i = 0; i < points.length; i++) {
                const next = (i + 1) % points.length;
                
                // Add sagging/drooping effect to rings
                const midX = (points[i].x + points[next].x) / 2;
                const midY = (points[i].y + points[next].y) / 2;
                const sag = (Math.random() - 0.3) * 8; // Slight downward sag
                
                this.strands.push({
                    type: 'ring',
                    x1: points[i].x,
                    y1: points[i].y,
                    x2: points[next].x,
                    y2: points[next].y,
                    midX: midX,
                    midY: midY + sag,
                    opacity: 0.15 + Math.random() * 0.25,
                    curved: true
                });
            }
            
            // Add some broken strands for realism
            if (Math.random() < 0.3 && points.length > 2) {
                const breakIndex = Math.floor(Math.random() * points.length);
                this.strands = this.strands.filter((_, idx) => 
                    !(idx === this.strands.length - points.length + breakIndex)
                );
            }
        }
    }

    draw(ctx) {
        this.strands.forEach(strand => {
            ctx.beginPath();
            ctx.moveTo(strand.x1, strand.y1);
            
            // Draw curved strands for organic feel
            if (strand.curved && strand.midX && strand.midY) {
                ctx.quadraticCurveTo(strand.midX, strand.midY, strand.x2, strand.y2);
            } else {
                ctx.lineTo(strand.x2, strand.y2);
            }
            
            ctx.strokeStyle = `rgba(57, 255, 20, ${strand.opacity})`;
            ctx.lineWidth = strand.type === 'spoke' ? 1.2 : 0.8;
            ctx.stroke();
            
            // Add subtle glow effect
            ctx.shadowBlur = 2;
            ctx.shadowColor = 'rgba(57, 255, 20, 0.4)';
            ctx.stroke();
            ctx.shadowBlur = 0;
        });
    }
}

class CrawlingSpider {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.size = 8 + Math.random() * 8;
        this.speed = 0.5 + Math.random() * 1;
        this.angle = Math.random() * Math.PI * 2;
        this.legPhase = 0;
        this.pauseTime = 0;
        this.isPaused = false;
        this.trailLength = 50;
        this.trail = [];
        
        // Depth animation (faster for more visible effect)
        this.depth = Math.random();
        this.depthSpeed = 0.004 + Math.random() * 0.006;
        this.depthDirection = Math.random() < 0.5 ? 1 : -1;
    }

    update() {
        if (this.isPaused) {
            this.pauseTime--;
            if (this.pauseTime <= 0) {
                this.isPaused = false;
                this.angle = Math.random() * Math.PI * 2;
            }
            // Still update depth when paused
            this.updateDepth();
            return;
        }

        // Random pause
        if (Math.random() < 0.01) {
            this.isPaused = true;
            this.pauseTime = 30 + Math.random() * 60;
            return;
        }

        // Update position
        this.x += Math.cos(this.angle) * this.speed;
        this.y += Math.sin(this.angle) * this.speed;

        // Add to trail
        this.trail.push({ x: this.x, y: this.y });
        if (this.trail.length > this.trailLength) {
            this.trail.shift();
        }

        // Bounce off edges
        if (this.x < 0 || this.x > window.innerWidth) {
            this.angle = Math.PI - this.angle;
            this.x = Math.max(0, Math.min(window.innerWidth, this.x));
        }
        if (this.y < 0 || this.y > window.innerHeight) {
            this.angle = -this.angle;
            this.y = Math.max(0, Math.min(window.innerHeight, this.y));
        }

        // Random direction change
        if (Math.random() < 0.02) {
            this.angle += (Math.random() - 0.5) * Math.PI / 2;
        }

        // Animate legs
        this.legPhase += 0.2;
        
        // Update depth
        this.updateDepth();
    }

    updateDepth() {
        // Depth animation (move between background and foreground)
        this.depth += this.depthSpeed * this.depthDirection;
        if (this.depth > 1) {
            this.depth = 1;
            this.depthDirection = -1;
        } else if (this.depth < 0) {
            this.depth = 0;
            this.depthDirection = 1;
        }
        
        // Scale based on depth (more dramatic)
        this.scale = 0.4 + this.depth * 1.2; // 0.4 to 1.6
    }

    draw(ctx) {
        // Calculate opacity based on depth (more dramatic)
        const depthOpacity = 0.3 + this.depth * 0.7;
        
        // Draw silk trail
        if (this.trail.length > 1) {
            ctx.beginPath();
            ctx.moveTo(this.trail[0].x, this.trail[0].y);
            for (let i = 1; i < this.trail.length; i++) {
                ctx.lineTo(this.trail[i].x, this.trail[i].y);
            }
            ctx.strokeStyle = `rgba(57, 255, 20, ${0.1 * depthOpacity})`;
            ctx.lineWidth = 1 * this.scale;
            ctx.stroke();
        }

        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.scale(this.scale, this.scale);
        ctx.rotate(this.angle);
        ctx.globalAlpha = depthOpacity;

        // Draw spider body
        ctx.fillStyle = '#39FF14';
        ctx.shadowBlur = 5;
        ctx.shadowColor = 'rgba(57, 255, 20, 0.8)';
        
        // Abdomen
        ctx.beginPath();
        ctx.ellipse(0, 0, this.size * 0.6, this.size * 0.8, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Cephalothorax
        ctx.beginPath();
        ctx.ellipse(this.size * 0.5, 0, this.size * 0.4, this.size * 0.5, 0, 0, Math.PI * 2);
        ctx.fill();

        // Draw legs
        ctx.strokeStyle = '#39FF14';
        ctx.lineWidth = 2;
        ctx.shadowBlur = 3;
        
        for (let i = 0; i < 4; i++) {
            const legAngle = (i - 1.5) * 0.4;
            const legLength = this.size * 1.5;
            const legBend = Math.sin(this.legPhase + i) * 0.3;
            
            // Left legs
            ctx.beginPath();
            ctx.moveTo(this.size * 0.3, 0);
            const midX1 = Math.cos(legAngle + legBend) * legLength * 0.6;
            const midY1 = Math.sin(legAngle + legBend) * legLength * 0.6 - this.size * 0.5;
            ctx.lineTo(midX1, midY1);
            const endX1 = Math.cos(legAngle) * legLength;
            const endY1 = Math.sin(legAngle) * legLength - this.size * 0.8;
            ctx.lineTo(endX1, endY1);
            ctx.stroke();
            
            // Right legs
            ctx.beginPath();
            ctx.moveTo(this.size * 0.3, 0);
            const midX2 = Math.cos(-legAngle - legBend) * legLength * 0.6;
            const midY2 = Math.sin(-legAngle - legBend) * legLength * 0.6 + this.size * 0.5;
            ctx.lineTo(midX2, midY2);
            const endX2 = Math.cos(-legAngle) * legLength;
            const endY2 = Math.sin(-legAngle) * legLength + this.size * 0.8;
            ctx.lineTo(endX2, endY2);
            ctx.stroke();
        }

        ctx.restore();
    }
}

class HangingSpider {
    constructor(x) {
        this.x = x;
        this.y = -50;
        this.targetY = 100 + Math.random() * 200;
        this.size = 10 + Math.random() * 12;
        this.speed = 0.5 + Math.random() * 0.8;
        this.state = 'descending'; // descending, hanging, ascending
        this.hangTime = 0;
        this.maxHangTime = 120 + Math.random() * 180;
        this.swingPhase = Math.random() * Math.PI * 2;
        this.swingSpeed = 0.02 + Math.random() * 0.03;
        this.swingAmplitude = 15 + Math.random() * 25;
        this.legPhase = 0;
        
        // Depth animation (faster for more visible effect)
        this.depth = Math.random();
        this.depthSpeed = 0.005 + Math.random() * 0.008;
        this.depthDirection = Math.random() < 0.5 ? 1 : -1;
    }

    update() {
        this.legPhase += 0.15;
        this.swingPhase += this.swingSpeed;
        
        // Depth animation
        this.depth += this.depthSpeed * this.depthDirection;
        if (this.depth > 1) {
            this.depth = 1;
            this.depthDirection = -1;
        } else if (this.depth < 0) {
            this.depth = 0;
            this.depthDirection = 1;
        }
        this.scale = 0.4 + this.depth * 1.2; // More dramatic scaling
        
        if (this.state === 'descending') {
            this.y += this.speed;
            if (this.y >= this.targetY) {
                this.state = 'hanging';
                this.hangTime = 0;
            }
        } else if (this.state === 'hanging') {
            this.hangTime++;
            if (this.hangTime >= this.maxHangTime) {
                this.state = 'ascending';
            }
        } else if (this.state === 'ascending') {
            this.y -= this.speed * 1.5;
            if (this.y < -50) {
                // Reset for next descent
                this.x = Math.random() * window.innerWidth;
                this.y = -50;
                this.targetY = 100 + Math.random() * 200;
                this.state = 'descending';
                this.hangTime = 0;
                this.maxHangTime = 120 + Math.random() * 180;
            }
        }
    }

    draw(ctx) {
        const swingOffset = Math.sin(this.swingPhase) * this.swingAmplitude;
        const currentX = this.x + swingOffset;
        const depthOpacity = 0.3 + this.depth * 0.7;
        
        // Draw silk strand
        ctx.beginPath();
        ctx.moveTo(this.x, 0);
        ctx.quadraticCurveTo(
            this.x + swingOffset * 0.5, this.y * 0.5,
            currentX, this.y
        );
        ctx.strokeStyle = `rgba(57, 255, 20, ${0.3 * depthOpacity})`;
        ctx.lineWidth = 1 * this.scale;
        ctx.stroke();
        
        // Add glow to strand
        ctx.shadowBlur = 3 * this.scale;
        ctx.shadowColor = `rgba(57, 255, 20, ${0.5 * depthOpacity})`;
        ctx.stroke();
        ctx.shadowBlur = 0;
        
        // Draw spider
        ctx.save();
        ctx.translate(currentX, this.y);
        ctx.scale(this.scale, this.scale);
        ctx.globalAlpha = depthOpacity;
        
        // Spider body
        ctx.fillStyle = '#39FF14';
        ctx.shadowBlur = 8;
        ctx.shadowColor = 'rgba(57, 255, 20, 0.9)';
        
        // Abdomen
        ctx.beginPath();
        ctx.ellipse(0, 0, this.size * 0.7, this.size * 0.9, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Cephalothorax
        ctx.beginPath();
        ctx.ellipse(0, -this.size * 0.6, this.size * 0.5, this.size * 0.6, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Red eyes
        ctx.fillStyle = '#DC143C';
        ctx.shadowBlur = 5;
        ctx.shadowColor = 'rgba(220, 20, 60, 0.8)';
        ctx.beginPath();
        ctx.arc(-this.size * 0.2, -this.size * 0.7, this.size * 0.15, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(this.size * 0.2, -this.size * 0.7, this.size * 0.15, 0, Math.PI * 2);
        ctx.fill();
        
        // Legs
        ctx.strokeStyle = '#39FF14';
        ctx.lineWidth = 2.5;
        ctx.shadowBlur = 4;
        ctx.shadowColor = 'rgba(57, 255, 20, 0.8)';
        
        for (let i = 0; i < 4; i++) {
            const legAngle = (i - 1.5) * 0.5;
            const legLength = this.size * 1.8;
            const legBend = Math.sin(this.legPhase + i) * 0.2;
            
            // Left legs
            ctx.beginPath();
            ctx.moveTo(0, -this.size * 0.3);
            const midX1 = Math.cos(legAngle + legBend - Math.PI / 2) * legLength * 0.6;
            const midY1 = Math.sin(legAngle + legBend - Math.PI / 2) * legLength * 0.6;
            ctx.lineTo(midX1, midY1);
            const endX1 = Math.cos(legAngle - Math.PI / 2) * legLength;
            const endY1 = Math.sin(legAngle - Math.PI / 2) * legLength;
            ctx.lineTo(endX1, endY1);
            ctx.stroke();
            
            // Right legs
            ctx.beginPath();
            ctx.moveTo(0, -this.size * 0.3);
            const midX2 = Math.cos(-legAngle - legBend - Math.PI / 2) * legLength * 0.6;
            const midY2 = Math.sin(-legAngle - legBend - Math.PI / 2) * legLength * 0.6;
            ctx.lineTo(midX2, midY2);
            const endX2 = Math.cos(-legAngle - Math.PI / 2) * legLength;
            const endY2 = Math.sin(-legAngle - Math.PI / 2) * legLength;
            ctx.lineTo(endX2, endY2);
            ctx.stroke();
        }
        
        ctx.restore();
    }
}

class JumpScareGhost {
    constructor() {
        this.startTime = Date.now();
        this.duration = 2000;
        this.size = 150;
        this.x = window.innerWidth / 2;
        this.y = window.innerHeight / 2;
        this.scale = 0;
        this.opacity = 0;
        this.eyeScale = 1;
        this.mouthOpen = 0;
    }

    update() {
        const elapsed = Date.now() - this.startTime;
        const progress = Math.min(elapsed / this.duration, 1);
        
        // Quick zoom in, hold, then fade out
        if (progress < 0.15) {
            // Fast zoom in
            this.scale = (progress / 0.15) * 4;
            this.opacity = (progress / 0.15);
        } else if (progress < 0.7) {
            // Hold and stare
            this.scale = 4;
            this.opacity = 1;
            // Eyes get bigger while staring
            this.eyeScale = 1 + Math.sin((progress - 0.15) * 20) * 0.3;
            // Mouth opens slowly
            this.mouthOpen = ((progress - 0.15) / 0.55) * 1;
        } else {
            // Fade out
            this.scale = 4 - ((progress - 0.7) / 0.3) * 2;
            this.opacity = 1 - ((progress - 0.7) / 0.3);
            this.eyeScale = 1.3;
            this.mouthOpen = 1;
        }
    }

    draw(ctx) {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.scale(this.scale, this.scale);
        ctx.globalAlpha = this.opacity;
        
        // Ghost body (sheet shape) - larger
        ctx.beginPath();
        ctx.moveTo(0, -this.size * 0.5);
        
        // Top rounded part (head)
        ctx.bezierCurveTo(
            -this.size * 0.5, -this.size * 0.5,
            -this.size * 0.5, this.size * 0.2,
            -this.size * 0.5, this.size * 0.2
        );
        
        // Bottom wavy part
        ctx.lineTo(-this.size * 0.5, this.size * 0.4);
        ctx.quadraticCurveTo(-this.size * 0.35, this.size * 0.5, -this.size * 0.25, this.size * 0.4);
        ctx.quadraticCurveTo(-this.size * 0.15, this.size * 0.3, 0, this.size * 0.4);
        ctx.quadraticCurveTo(this.size * 0.15, this.size * 0.5, this.size * 0.25, this.size * 0.4);
        ctx.quadraticCurveTo(this.size * 0.35, this.size * 0.3, this.size * 0.5, this.size * 0.4);
        
        ctx.lineTo(this.size * 0.5, this.size * 0.2);
        ctx.bezierCurveTo(
            this.size * 0.5, this.size * 0.2,
            this.size * 0.5, -this.size * 0.5,
            0, -this.size * 0.5
        );
        
        ctx.closePath();
        
        // Bright white ghost
        ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
        ctx.fill();
        
        // Intense glow
        ctx.shadowBlur = 50;
        ctx.shadowColor = 'rgba(255, 255, 255, 1)';
        ctx.fill();
        ctx.shadowBlur = 0;
        
        // HUGE STARING EYES
        ctx.save();
        ctx.scale(this.eyeScale, this.eyeScale);
        
        // Left eye - HUGE and BLACK
        ctx.fillStyle = 'rgba(0, 0, 0, 1)';
        ctx.beginPath();
        ctx.ellipse(-this.size * 0.18, -this.size * 0.15, this.size * 0.15, this.size * 0.22, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Right eye - HUGE and BLACK
        ctx.beginPath();
        ctx.ellipse(this.size * 0.18, -this.size * 0.15, this.size * 0.15, this.size * 0.22, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Eye whites/highlights for intensity
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.beginPath();
        ctx.arc(-this.size * 0.18, -this.size * 0.18, this.size * 0.05, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(this.size * 0.18, -this.size * 0.18, this.size * 0.05, 0, Math.PI * 2);
        ctx.fill();
        
        // Red glow in eyes for horror
        ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
        ctx.shadowBlur = 20;
        ctx.shadowColor = 'rgba(255, 0, 0, 0.8)';
        ctx.beginPath();
        ctx.arc(-this.size * 0.18, -this.size * 0.15, this.size * 0.08, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(this.size * 0.18, -this.size * 0.15, this.size * 0.08, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
        
        ctx.restore();
        
        // MOUTH - Opens wide in horror scream
        ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
        ctx.beginPath();
        const mouthHeight = this.size * 0.12 * this.mouthOpen;
        ctx.ellipse(0, this.size * 0.05, this.size * 0.1, mouthHeight, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Mouth glow
        if (this.mouthOpen > 0.5) {
            ctx.shadowBlur = 15;
            ctx.shadowColor = 'rgba(0, 0, 0, 0.8)';
            ctx.fill();
            ctx.shadowBlur = 0;
        }
        
        ctx.restore();
    }
}

class JumpScareSpider {
    constructor() {
        this.startTime = Date.now();
        this.duration = 1500;
        this.size = 80;
        this.x = window.innerWidth / 2;
        this.y = window.innerHeight / 2;
        this.legPhase = 0;
        this.scale = 0;
        this.opacity = 0;
        this.rotation = 0;
    }

    update() {
        const elapsed = Date.now() - this.startTime;
        const progress = Math.min(elapsed / this.duration, 1);
        
        // Quick zoom in, then fade out
        if (progress < 0.3) {
            this.scale = (progress / 0.3) * 3;
            this.opacity = (progress / 0.3);
        } else {
            this.scale = 3 - ((progress - 0.3) / 0.7) * 2;
            this.opacity = 1 - ((progress - 0.3) / 0.7);
        }
        
        this.legPhase += 0.5;
        this.rotation = Math.sin(progress * Math.PI * 4) * 0.2;
    }

    draw(ctx) {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.scale(this.scale, this.scale);
        ctx.rotate(this.rotation);
        ctx.globalAlpha = this.opacity;
        
        // Giant spider body
        ctx.fillStyle = '#39FF14';
        ctx.shadowBlur = 30;
        ctx.shadowColor = 'rgba(57, 255, 20, 1)';
        
        // Abdomen
        ctx.beginPath();
        ctx.ellipse(0, 0, this.size * 0.7, this.size * 0.9, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Cephalothorax
        ctx.beginPath();
        ctx.ellipse(0, -this.size * 0.6, this.size * 0.5, this.size * 0.6, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // GLOWING RED EYES
        ctx.fillStyle = '#FF0000';
        ctx.shadowBlur = 20;
        ctx.shadowColor = 'rgba(255, 0, 0, 1)';
        ctx.beginPath();
        ctx.arc(-this.size * 0.25, -this.size * 0.7, this.size * 0.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(this.size * 0.25, -this.size * 0.7, this.size * 0.2, 0, Math.PI * 2);
        ctx.fill();
        
        // Menacing legs
        ctx.strokeStyle = '#39FF14';
        ctx.lineWidth = 6;
        ctx.shadowBlur = 15;
        ctx.shadowColor = 'rgba(57, 255, 20, 1)';
        
        for (let i = 0; i < 4; i++) {
            const legAngle = (i - 1.5) * 0.6;
            const legLength = this.size * 2.5;
            const legBend = Math.sin(this.legPhase + i) * 0.4;
            
            // Left legs
            ctx.beginPath();
            ctx.moveTo(0, -this.size * 0.3);
            const midX1 = Math.cos(legAngle + legBend - Math.PI / 2) * legLength * 0.6;
            const midY1 = Math.sin(legAngle + legBend - Math.PI / 2) * legLength * 0.6;
            ctx.lineTo(midX1, midY1);
            const endX1 = Math.cos(legAngle - Math.PI / 2) * legLength;
            const endY1 = Math.sin(legAngle - Math.PI / 2) * legLength;
            ctx.lineTo(endX1, endY1);
            ctx.stroke();
            
            // Right legs
            ctx.beginPath();
            ctx.moveTo(0, -this.size * 0.3);
            const midX2 = Math.cos(-legAngle - legBend - Math.PI / 2) * legLength * 0.6;
            const midY2 = Math.sin(-legAngle - legBend - Math.PI / 2) * legLength * 0.6;
            ctx.lineTo(midX2, midY2);
            const endX2 = Math.cos(-legAngle - Math.PI / 2) * legLength;
            const endY2 = Math.sin(-legAngle - Math.PI / 2) * legLength;
            ctx.lineTo(endX2, endY2);
            ctx.stroke();
        }
        
        ctx.restore();
    }
}

class FogParticle {
    constructor() {
        this.reset();
        // Start at random position for initial state
        this.y = Math.random() * window.innerHeight;
        this.opacity = Math.random() * 0.3;
    }

    reset() {
        this.x = Math.random() * window.innerWidth;
        this.y = -100;
        this.size = 150 + Math.random() * 250; // Large fog clouds
        this.speedY = 0.2 + Math.random() * 0.4; // Slow drift down
        this.speedX = (Math.random() - 0.5) * 0.3; // Slight horizontal drift
        this.opacity = 0;
        this.targetOpacity = 0.15 + Math.random() * 0.25;
        this.pulseSpeed = 0.001 + Math.random() * 0.002;
        this.pulsePhase = Math.random() * Math.PI * 2;
        this.color = Math.random() < 0.5 ? 
            'rgba(106, 13, 173, ' : // Purple fog
            'rgba(57, 255, 20, '; // Green fog
    }

    update() {
        // Drift movement
        this.y += this.speedY;
        this.x += this.speedX;
        
        // Pulsing opacity
        this.pulsePhase += this.pulseSpeed;
        const pulseFactor = Math.sin(this.pulsePhase) * 0.5 + 0.5;
        
        // Fade in
        if (this.opacity < this.targetOpacity) {
            this.opacity += 0.002;
        }
        
        this.currentOpacity = this.opacity * (0.7 + pulseFactor * 0.3);
        
        // Wrap around edges
        if (this.x < -this.size) this.x = window.innerWidth + this.size;
        if (this.x > window.innerWidth + this.size) this.x = -this.size;
        
        // Reset when off screen
        if (this.y > window.innerHeight + this.size) {
            this.reset();
        }
    }

    draw(ctx) {
        ctx.save();
        
        // Create radial gradient for fog
        const gradient = ctx.createRadialGradient(
            this.x, this.y, 0,
            this.x, this.y, this.size
        );
        
        gradient.addColorStop(0, this.color + (this.currentOpacity * 0.8) + ')');
        gradient.addColorStop(0.4, this.color + (this.currentOpacity * 0.4) + ')');
        gradient.addColorStop(1, this.color + '0)');
        
        ctx.fillStyle = gradient;
        ctx.filter = 'blur(40px)';
        ctx.fillRect(
            this.x - this.size,
            this.y - this.size,
            this.size * 2,
            this.size * 2
        );
        
        ctx.restore();
    }
}

class FloatingGhost {
    constructor() {
        this.reset();
        // Start at random position for initial state
        this.x = Math.random() * window.innerWidth;
        this.y = Math.random() * window.innerHeight;
        this.opacity = Math.random() * 0.3;
    }

    reset() {
        // Start from random edge
        const edge = Math.floor(Math.random() * 4);
        switch(edge) {
            case 0: // Top
                this.x = Math.random() * window.innerWidth;
                this.y = -100;
                break;
            case 1: // Right
                this.x = window.innerWidth + 100;
                this.y = Math.random() * window.innerHeight;
                break;
            case 2: // Bottom
                this.x = Math.random() * window.innerWidth;
                this.y = window.innerHeight + 100;
                break;
            case 3: // Left
                this.x = -100;
                this.y = Math.random() * window.innerHeight;
                break;
        }
        
        this.size = 40 + Math.random() * 40;
        this.speedX = (Math.random() - 0.5) * 0.8;
        this.speedY = (Math.random() - 0.5) * 0.8;
        this.opacity = 0;
        this.targetOpacity = 0.3 + Math.random() * 0.4;
        this.floatPhase = Math.random() * Math.PI * 2;
        this.floatSpeed = 0.02 + Math.random() * 0.03;
        this.floatAmplitude = 10 + Math.random() * 20;
        this.rotation = Math.random() * Math.PI * 2;
        this.rotationSpeed = (Math.random() - 0.5) * 0.02;
        this.pulsePhase = Math.random() * Math.PI * 2;
        this.pulseSpeed = 0.03 + Math.random() * 0.02;
        
        // Depth animation (z-axis simulation)
        this.depth = Math.random(); // 0 = far, 1 = near
        this.depthSpeed = 0.003 + Math.random() * 0.005;
        this.depthDirection = Math.random() < 0.5 ? 1 : -1;
        
        // Random ghost color
        const colors = [
            'rgba(255, 255, 255, ',  // White ghost
            'rgba(200, 255, 200, ',  // Green ghost
            'rgba(200, 200, 255, ',  // Blue ghost
            'rgba(255, 200, 255, '   // Purple ghost
        ];
        this.color = colors[Math.floor(Math.random() * colors.length)];
    }

    update() {
        // Floating movement
        this.floatPhase += this.floatSpeed;
        this.pulsePhase += this.pulseSpeed;
        
        const floatOffsetX = Math.sin(this.floatPhase) * this.floatAmplitude;
        const floatOffsetY = Math.cos(this.floatPhase * 0.7) * this.floatAmplitude;
        
        this.x += this.speedX + floatOffsetX * 0.1;
        this.y += this.speedY + floatOffsetY * 0.1;
        
        // Rotation
        this.rotation += this.rotationSpeed;
        
        // Depth animation (move between background and foreground)
        this.depth += this.depthSpeed * this.depthDirection;
        if (this.depth > 1) {
            this.depth = 1;
            this.depthDirection = -1;
        } else if (this.depth < 0) {
            this.depth = 0;
            this.depthDirection = 1;
        }
        
        // Scale based on depth (closer = MUCH bigger for dramatic effect)
        this.scale = 0.3 + this.depth * 1.5; // 0.3 to 1.8 (more dramatic)
        
        // Fade in
        if (this.opacity < this.targetOpacity) {
            this.opacity += 0.005;
        }
        
        // Pulsing opacity (also affected by depth)
        const pulseFactor = Math.sin(this.pulsePhase) * 0.5 + 0.5;
        const depthOpacity = 0.2 + this.depth * 0.8; // Far = very transparent, near = opaque
        this.currentOpacity = this.opacity * (0.5 + pulseFactor * 0.5) * depthOpacity;
        
        // Reset when off screen
        if (this.x < -150 || this.x > window.innerWidth + 150 ||
            this.y < -150 || this.y > window.innerHeight + 150) {
            this.reset();
        }
    }

    draw(ctx) {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.scale(this.scale, this.scale); // Apply depth scaling
        ctx.rotate(this.rotation);
        ctx.globalAlpha = this.currentOpacity;
        
        // Ghost body (sheet shape)
        ctx.beginPath();
        ctx.moveTo(0, -this.size * 0.5);
        
        // Top rounded part (head)
        ctx.bezierCurveTo(
            -this.size * 0.5, -this.size * 0.5,
            -this.size * 0.5, this.size * 0.2,
            -this.size * 0.5, this.size * 0.2
        );
        
        // Bottom wavy part
        ctx.lineTo(-this.size * 0.5, this.size * 0.4);
        ctx.quadraticCurveTo(-this.size * 0.35, this.size * 0.5, -this.size * 0.25, this.size * 0.4);
        ctx.quadraticCurveTo(-this.size * 0.15, this.size * 0.3, 0, this.size * 0.4);
        ctx.quadraticCurveTo(this.size * 0.15, this.size * 0.5, this.size * 0.25, this.size * 0.4);
        ctx.quadraticCurveTo(this.size * 0.35, this.size * 0.3, this.size * 0.5, this.size * 0.4);
        
        ctx.lineTo(this.size * 0.5, this.size * 0.2);
        ctx.bezierCurveTo(
            this.size * 0.5, this.size * 0.2,
            this.size * 0.5, -this.size * 0.5,
            0, -this.size * 0.5
        );
        
        ctx.closePath();
        
        // Gradient fill
        const gradient = ctx.createRadialGradient(0, -this.size * 0.2, 0, 0, 0, this.size * 0.6);
        gradient.addColorStop(0, this.color + '0.9)');
        gradient.addColorStop(0.5, this.color + '0.6)');
        gradient.addColorStop(1, this.color + '0.2)');
        
        ctx.fillStyle = gradient;
        ctx.fill();
        
        // Outer glow
        ctx.shadowBlur = 20;
        ctx.shadowColor = this.color + '0.8)';
        ctx.fill();
        
        // Eyes
        ctx.shadowBlur = 0;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        
        // Left eye
        ctx.beginPath();
        ctx.ellipse(-this.size * 0.15, -this.size * 0.15, this.size * 0.08, this.size * 0.12, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Right eye
        ctx.beginPath();
        ctx.ellipse(this.size * 0.15, -this.size * 0.15, this.size * 0.08, this.size * 0.12, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Eye highlights
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.beginPath();
        ctx.arc(-this.size * 0.15, -this.size * 0.18, this.size * 0.03, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(this.size * 0.15, -this.size * 0.18, this.size * 0.03, 0, Math.PI * 2);
        ctx.fill();
        
        // Mouth (O shape)
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.beginPath();
        ctx.ellipse(0, this.size * 0.05, this.size * 0.06, this.size * 0.08, 0, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
    }
}

class FloatingPumpkin {
    constructor() {
        this.reset();
        this.x = Math.random() * window.innerWidth;
        this.y = Math.random() * window.innerHeight;
        this.opacity = Math.random() * 0.3;
    }

    reset() {
        const edge = Math.floor(Math.random() * 4);
        switch(edge) {
            case 0: this.x = Math.random() * window.innerWidth; this.y = -100; break;
            case 1: this.x = window.innerWidth + 100; this.y = Math.random() * window.innerHeight; break;
            case 2: this.x = Math.random() * window.innerWidth; this.y = window.innerHeight + 100; break;
            case 3: this.x = -100; this.y = Math.random() * window.innerHeight; break;
        }
        
        this.size = 40;
        this.speedX = (Math.random() - 0.5) * 0.6;
        this.speedY = (Math.random() - 0.5) * 0.6;
        this.opacity = 0;
        this.targetOpacity = 0.5 + Math.random() * 0.4;
        this.bobPhase = Math.random() * Math.PI * 2;
        this.bobSpeed = 0.03 + Math.random() * 0.02;
        this.bobAmplitude = 8 + Math.random() * 12;
        this.rotation = (Math.random() - 0.5) * 0.3;
        this.rotationSpeed = (Math.random() - 0.5) * 0.01;
        
        // Depth animation
        this.depth = Math.random();
        this.depthSpeed = 0.004 + Math.random() * 0.006;
        this.depthDirection = Math.random() < 0.5 ? 1 : -1;
    }

    update() {
        this.bobPhase += this.bobSpeed;
        
        const bobOffsetX = Math.sin(this.bobPhase) * this.bobAmplitude;
        const bobOffsetY = Math.cos(this.bobPhase * 0.8) * this.bobAmplitude;
        
        this.x += this.speedX + bobOffsetX * 0.08;
        this.y += this.speedY + bobOffsetY * 0.08;
        this.rotation += this.rotationSpeed;
        
        // Depth animation
        this.depth += this.depthSpeed * this.depthDirection;
        if (this.depth > 1) {
            this.depth = 1;
            this.depthDirection = -1;
        } else if (this.depth < 0) {
            this.depth = 0;
            this.depthDirection = 1;
        }
        this.scale = 0.4 + this.depth * 1.8;
        
        if (this.opacity < this.targetOpacity) {
            this.opacity += 0.005;
        }
        
        const depthOpacity = 0.3 + this.depth * 0.7;
        this.currentOpacity = this.opacity * depthOpacity;
        
        if (this.x < -150 || this.x > window.innerWidth + 150 ||
            this.y < -150 || this.y > window.innerHeight + 150) {
            this.reset();
        }
    }

    draw(ctx) {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.scale(this.scale, this.scale);
        ctx.rotate(this.rotation);
        ctx.globalAlpha = this.currentOpacity;
        
        // Draw pumpkin emoji
        ctx.font = `${this.size}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Add glow effect
        ctx.shadowBlur = 15;
        ctx.shadowColor = 'rgba(255, 140, 0, 0.8)';
        
        ctx.fillText('🎃', 0, 0);
        
        ctx.restore();
    }
}

class JumpScarePumpkin {
    constructor() {
        this.startTime = Date.now();
        this.duration = 2200;
        this.size = 200;
        this.x = window.innerWidth / 2;
        this.y = window.innerHeight / 2;
        this.scale = 0;
        this.opacity = 0;
        this.shakeAmount = 0;
    }

    update() {
        const elapsed = Date.now() - this.startTime;
        const progress = Math.min(elapsed / this.duration, 1);
        
        if (progress < 0.2) {
            // Fast zoom in
            this.scale = (progress / 0.2) * 5;
            this.opacity = (progress / 0.2);
        } else if (progress < 0.75) {
            // Hold and shake
            this.scale = 5;
            this.opacity = 1;
            this.shakeAmount = Math.sin((progress - 0.2) * 50) * 5;
        } else {
            // Fade out
            this.scale = 5 - ((progress - 0.75) / 0.25) * 2;
            this.opacity = 1 - ((progress - 0.75) / 0.25);
            this.shakeAmount = 8;
        }
    }

    draw(ctx) {
        ctx.save();
        ctx.translate(this.x + this.shakeAmount, this.y);
        ctx.scale(this.scale, this.scale);
        ctx.globalAlpha = this.opacity;
        
        // Draw pumpkin emoji with intense glow
        ctx.font = `${this.size}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Intense glow
        ctx.shadowBlur = 80;
        ctx.shadowColor = 'rgba(255, 140, 0, 1)';
        
        ctx.fillText('🎃', 0, 0);
        
        // Extra glow layer
        ctx.shadowBlur = 120;
        ctx.shadowColor = 'rgba(255, 100, 0, 0.8)';
        ctx.fillText('🎃', 0, 0);
        
        ctx.restore();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const webSystem = new SpiderWebSystem();
        webSystem.init();
    });
} else {
    const webSystem = new SpiderWebSystem();
    webSystem.init();
}
