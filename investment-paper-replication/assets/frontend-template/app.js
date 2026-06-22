const canvas = document.getElementById("performanceChart");
const ctx = canvas.getContext("2d");

const series = [
  100, 104, 108, 113, 117, 121, 126, 124, 130, 135, 143, 148, 151, 159, 166,
  171, 168, 176, 184, 191, 199, 206, 211, 218, 225, 229, 233, 238, 241, 244
];

function drawChart() {
  const width = canvas.width;
  const height = canvas.height;
  const padding = { top: 28, right: 34, bottom: 38, left: 54 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const min = 95;
  const max = 250;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#fbfcfd";
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "#d7dde2";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#66707a";
  ctx.font = "12px Amplitude, Arial, sans-serif";

  for (let i = 0; i <= 5; i += 1) {
    const y = padding.top + (chartHeight / 5) * i;
    const value = Math.round(max - ((max - min) / 5) * i);
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
    ctx.fillText(String(value), 14, y + 4);
  }

  const points = series.map((value, index) => {
    const x = padding.left + (chartWidth / (series.length - 1)) * index;
    const y = padding.top + chartHeight - ((value - min) / (max - min)) * chartHeight;
    return { x, y };
  });

  ctx.strokeStyle = "#2f5e88";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  points.forEach((point, index) => {
    if (index === 0) {
      ctx.moveTo(point.x, point.y);
    } else {
      ctx.lineTo(point.x, point.y);
    }
  });
  ctx.stroke();

  ctx.fillStyle = "#936846";
  points.slice(-1).forEach((point) => {
    ctx.beginPath();
    ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
    ctx.fill();
  });

  ctx.fillStyle = "#31373d";
  ctx.font = "400 13px Amplitude, Arial, sans-serif";
  ctx.fillText("累计收益指数（未扣交易成本）", padding.left, 22);
}

drawChart();
