(() => {
  let rec = false;
  const recBtn = document.getElementById("recBtn");
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`);

  if (recBtn) {
    recBtn.addEventListener("click", () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "rec", on: !rec }));
      }
    });
  }

  ws.addEventListener("open", () => {
    // 연결됨
  });

  ws.addEventListener("message", (ev) => {
    // 서버에서 브로드캐스트된 JSON(다른 클라이언트 조이스틱 등)
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === "joystick") {
        // 필요하면 여기서 msg.x, msg.y, msg.strength, msg.angleDeg 활용
        // console.log("peer joystick:", msg);
      }
      if (msg.type === "frame") {
        const live = document.getElementById("live");
        if (live) {
          live.src = "data:image/jpeg;base64," + msg.jpegBase64;
        }
        return;
      }
      if (msg.type === "rec") {
        rec = !!msg.on;
        if (recBtn) {
          recBtn.textContent = rec ? "⏹ Stop Recording" : "⏺ Start Recording";
          recBtn.style.background = rec ? "#b00020" : "#222";
        }
        return;
      }
    } catch (_) {
      // 일반 텍스트 수신일 수도 있음
    }
  });

  const JOYSTICK_HZ = 60; // 조이스틱 폴링레이트
  let latest = { angleDeg: 0, strength: 0, x: 0, y: 0, angleRad: 0 };

  // 10Hz로 현재 조이스틱 스냅샷을 항상 전송 (정지 중이면 0,0을 계속 보냄)
  setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(
        JSON.stringify({
          type: "joystick",
          angleRad: latest.angleRad,
          angleDeg: latest.angleDeg,
          strength: latest.strength,
          x: latest.x,
          y: latest.y,
          t: Date.now(),
        })
      );
    }
  }, 1000 / JOYSTICK_HZ);

  const el = document.getElementById("joystick");
  const knob = document.getElementById("stick");
  const angleEl = document.getElementById("angle");
  const strengthEl = document.getElementById("strength");
  const vecEl = document.getElementById("vec");

  /** 상태 */
  let activeId = null;
  let rect = null;
  let center = { x: 0, y: 0 };
  let radiusPx = 0; // 바닥 원 반지름 (픽셀)
  let maxDx = 0,
    maxDy = 0; // 이동 한계 (x,y 방향 동일)

  /** 초기 레이아웃 측정 */
  function measure() {
    rect = el.getBoundingClientRect(); // 뷰포트 기준 위치/크기
    const size = Math.min(rect.width, rect.height);
    const knobSize =
      knob.getBoundingClientRect().width ||
      parseFloat(getComputedStyle(knob).width);
    radiusPx = (size - knobSize) / 2; // 손잡이 가장자리 기준으로 안에서만 이동
    center.x = rect.left + rect.width / 2;
    center.y = rect.top + rect.height / 2;
    maxDx = maxDy = radiusPx;
  }
  measure();
  window.addEventListener("resize", measure);

  /** 좌표 → 조이스틱 값 계산 */
  function computeValues(px, py) {
    // 뷰포트 좌표를 조이스틱 중심 기준으로 변환
    let dx = px - center.x;
    let dy = py - center.y;

    // 반지름 내로 클램프
    const dist = Math.hypot(dx, dy);
    const clamped = Math.min(dist, radiusPx);
    const angRad = Math.atan2(dy, dx); // +x를 0rad, 반시계(+y 아래) 기준
    const ux = Math.cos(angRad);
    const uy = Math.sin(angRad);
    const cx = ux * clamped;
    const cy = uy * clamped;

    // 정규화 벡터(−1..1), y는 위가 +가 되도록 반전
    const nx = cx / radiusPx;
    const ny = -cy / radiusPx;

    // 세기(0..1)
    const strength = Math.min(dist / radiusPx, 1);

    // 각도(deg) 0..360 (0=오른쪽, 90=아래, 180=왼쪽, 270=위)
    let deg = (angRad * 180) / Math.PI;
    if (deg < 0) deg += 360;

    return {
      cx,
      cy,
      nx,
      ny,
      strength,
      angleRad: angRad,
      angleDeg: deg,
    };
  }

  /** 손잡이 위치 업데이트 + 출력 */
  function render(val) {
    // CSS transform으로 이동
    knob.style.transform = `translate(${val.cx}px, ${val.cy}px)`;

    // 화면 표시
    angleEl.textContent = val.angleDeg.toFixed(1);
    strengthEl.textContent = val.strength.toFixed(2);
    vecEl.textContent = `${val.nx.toFixed(2)}, ${val.ny.toFixed(2)}`;

    // ARIA 값 갱신
    knob.setAttribute("aria-valuenow", val.strength.toFixed(2));

    // 커스텀 이벤트 발행 (리스너에서 게임/컨트롤 로직에 사용)
    const evt = new CustomEvent("joystick", {
      detail: {
        angleRad: val.angleRad,
        angleDeg: val.angleDeg,
        strength: val.strength,
        x: val.nx, // 오른쪽 +, 왼쪽 −
        y: val.ny, // 위 +, 아래 −
      },
    });
    el.dispatchEvent(evt);
  }

  /** 중앙 복귀 */
  function snapCenter() {
    const zero = {
      cx: 0,
      cy: 0,
      nx: 0,
      ny: 0,
      strength: 0,
      angleRad: 0,
      angleDeg: 0,
    };
    render(zero);
  }

  /** 포인터 이벤트 핸들러 */
  function onDown(e) {
    e.preventDefault();
    activeId = e.pointerId;
    knob.releasePointerCapture?.(activeId); // 혹시 이전 캡처가 남아있으면 해제
    knob.setPointerCapture?.(activeId); // 드래그가 밖으로 나가도 우리 엘리먼트로 이벤트 고정
    knob.style.transition = "transform 0ms linear"; // 드래그 중에는 즉시 반응
    measure(); // 최신 중심/반지름 재계산

    const v = computeValues(e.clientX, e.clientY);
    render(v);
  }

  function onMove(e) {
    if (e.pointerId !== activeId) return;
    const v = computeValues(e.clientX, e.clientY);
    render(v);
  }

  function onUpOrCancel(e) {
    if (e.pointerId !== activeId) return;
    activeId = null;
    knob.releasePointerCapture?.(e.pointerId);
    knob.style.transition = "transform 120ms ease-out"; // 부드럽게 중앙 복귀
    snapCenter();
  }

  // 리스너 등록 (Pointer Events 단일 모델)
  knob.addEventListener("pointerdown", onDown);
  window.addEventListener("pointermove", onMove, { passive: true });
  window.addEventListener("pointerup", onUpOrCancel);
  window.addEventListener("pointercancel", onUpOrCancel);

  // 초기 상태
  snapCenter();

  // 외부에서 값 구독
  el.addEventListener("joystick", (e) => {
    const { angleRad, angleDeg, strength, x, y } = e.detail;
    latest.angleRad = angleRad;
    latest.angleDeg = angleDeg;
    latest.strength = strength;
    latest.x = x;
    latest.y = y;
  });
})();
