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

  const initializeChart = (canvasId, chartType, labelText, color) => {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === 'undefined') return;

    const labels = JSON.parse(canvas.dataset.labels || '[]');
    const values = JSON.parse(canvas.dataset.values || '[]');
    const hasData = values.length > 0 && labels.length > 0;

    if (!hasData) {
      const parent = canvas.closest('.chart-canvas-wrap');
      if (parent) {
        parent.innerHTML = '<div class="chart-empty">No data available for this filter set.</div>';
      }
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
            grid: { color: 'rgba(12, 68, 152, 0.12)' },
            ticks: { color: '#475569', beginAtZero: true }
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
