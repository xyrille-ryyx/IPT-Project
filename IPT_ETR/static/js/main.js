document.addEventListener('DOMContentLoaded', () => {
  const toggles = document.querySelectorAll('.password-toggle');

  toggles.forEach(toggle => {
    const targets = toggle.dataset.targets ? toggle.dataset.targets.split(' ') : [toggle.dataset.target];
    const inputs = targets
      .map(id => document.getElementById(id))
      .filter(Boolean);

    if (!inputs.length) {
      return;
    }

    toggle.addEventListener('change', () => {
      const show = toggle.checked;
      inputs.forEach(input => {
        input.type = show ? 'text' : 'password';
      });
    });
  });

  const profileForm = document.getElementById('profile-form');
  const saveProfileButton = document.getElementById('saveProfileButton');
  const profileFeedback = document.getElementById('profileFeedback');

  let profileInitial = {};
  if (profileForm) {
    Array.from(profileForm.elements).forEach(element => {
      if (element.name && ['new_username', 'current_password', 'new_password', 'confirm_password'].includes(element.name)) {
        profileInitial[element.name] = element.value || '';
      }
    });
  }

  const isProfileDirty = () => {
    if (!profileForm) return false;
    return Array.from(profileForm.elements).some(element => {
      if (element.name && profileInitial.hasOwnProperty(element.name)) {
        return (element.value || '') !== (profileInitial[element.name] || '');
      }
      return false;
    });
  };

  if (saveProfileButton) {
    saveProfileButton.addEventListener('click', () => {
      if (!isProfileDirty()) {
        if (profileFeedback) {
          profileFeedback.textContent = 'Make a change before saving your profile.';
        }
        return;
      }
      if (profileFeedback) {
        profileFeedback.textContent = '';
      }
      if (profileForm) {
        profileForm.submit();
      }
    });
  }

  const getChartData = canvas => {
    try {
      return {
        labels: JSON.parse(canvas.dataset.labels || '[]'),
        values: JSON.parse(canvas.dataset.values || '[]')
      };
    } catch (error) {
      console.error(`Could not parse chart data for #${canvas.id}`, error);
      return { labels: [], values: [] };
    }
  };

  const drawFallbackChart = (canvas, chartType, labels, values, color) => {
    const wrapper = canvas.closest('.chart-canvas-wrap');
    const width = wrapper ? wrapper.clientWidth : canvas.clientWidth;
    const height = wrapper ? wrapper.clientHeight : canvas.clientHeight;
    const scale = window.devicePixelRatio || 1;

    canvas.width = Math.max(width, 1) * scale;
    canvas.height = Math.max(height, 1) * scale;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.setTransform(scale, 0, 0, scale, 0, 0);
    ctx.clearRect(0, 0, width, height);

    const padding = { top: 28, right: 24, bottom: 44, left: 48 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const maxValue = Math.max(...values.map(Number), 1);
    const barGap = 12;
    const barWidth = Math.max((chartWidth - barGap * (labels.length - 1)) / labels.length, 12);
    const axisColor = '#CBD5E1';
    const textColor = '#475569';

    ctx.strokeStyle = axisColor;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, padding.top + chartHeight);
    ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
    ctx.stroke();

    ctx.fillStyle = textColor;
    ctx.font = '12px Inter, system-ui, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(String(Math.ceil(maxValue)), padding.left - 10, padding.top + 4);
    ctx.fillText('0', padding.left - 10, padding.top + chartHeight + 4);

    if (chartType === 'line') {
      const step = labels.length > 1 ? chartWidth / (labels.length - 1) : chartWidth;

      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.beginPath();

      values.forEach((rawValue, index) => {
        const x = padding.left + (labels.length > 1 ? index * step : chartWidth / 2);
        const y = padding.top + chartHeight - (Number(rawValue) / maxValue) * chartHeight;
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();

      values.forEach((rawValue, index) => {
        const x = padding.left + (labels.length > 1 ? index * step : chartWidth / 2);
        const y = padding.top + chartHeight - (Number(rawValue) / maxValue) * chartHeight;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
      });
    } else {
      values.forEach((rawValue, index) => {
        const barHeight = (Number(rawValue) / maxValue) * chartHeight;
        const x = padding.left + index * (barWidth + barGap);
        const y = padding.top + chartHeight - barHeight;

        ctx.fillStyle = 'rgba(12, 68, 152, 0.35)';
        ctx.fillRect(x, y, barWidth, barHeight);
        ctx.strokeStyle = color;
        ctx.strokeRect(x, y, barWidth, barHeight);
      });
    }

    ctx.fillStyle = textColor;
    ctx.textAlign = 'center';
    labels.forEach((label, index) => {
      const x = chartType === 'bar'
        ? padding.left + index * (barWidth + barGap) + barWidth / 2
        : labels.length > 1
          ? padding.left + index * (chartWidth / (labels.length - 1))
          : padding.left + chartWidth / 2;
      ctx.fillText(label, x, padding.top + chartHeight + 24);
    });
  };

  const initializeChart = (canvasId, chartType, labelText, color) => {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const { labels, values } = getChartData(canvas);
    const hasData = values.length > 0 && labels.length > 0;

    if (!hasData) {
      const parent = canvas.closest('.chart-canvas-wrap');
      if (parent) {
        parent.innerHTML = '<div class="chart-empty">No data available for this filter set.</div>';
      }
      return;
    }

    if (typeof Chart === 'undefined') {
      drawFallbackChart(canvas, chartType, labels, values, color);
      return;
    }

    new Chart(canvas, {
      type: chartType,
      data: {
        labels,
        datasets: [{
          label: labelText,
          data: values,
          borderColor: color,
          backgroundColor: chartType === 'bar' ? values.map(() => 'rgba(12, 68, 152, 0.35)') : 'rgba(12, 68, 152, 0.25)',
          borderWidth: 2,
          fill: chartType === 'line',
          tension: 0.35,
          pointRadius: chartType === 'line' ? 4 : 0,
          pointBackgroundColor: '#0C4498',
          hoverBackgroundColor: '#0A3B82',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            enabled: true,
            backgroundColor: '#102A43',
            titleColor: '#FFFFFF',
            bodyColor: '#F8FAFF',
            cornerRadius: 12,
            padding: 12,
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#475569' }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(12, 68, 152, 0.12)' },
            ticks: { color: '#475569' }
          }
        }
      }
    });
  };

  initializeChart('stressChart', 'bar', 'Stress count', '#0C4498');
  initializeChart('sleepChart', 'line', 'Average sleep hours', '#0C4498');

  const successToastEl = document.querySelector('.successToast');
  if (successToastEl && typeof bootstrap !== 'undefined') {
    const toast = new bootstrap.Toast(successToastEl, { delay: 3800 });
    toast.show();
  }
});
