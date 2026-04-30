let chart = null;
let lineSeries = null;
let currentGallery = 'us-stocks';
let currentTimeframe = '7D';

// API 기본 URL (환경에 맞게 조정)
const API_BASE_URL = '/api';

function initChart() {
    const container = document.getElementById('chart-container');
    container.innerHTML = '';

    chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: container.clientHeight,
        layout: {
            background: { type: 'solid', color: '#ffffff' },
            textColor: '#333333'
        },
        grid: {
            vertLines: { color: '#e0e0e0' },
            horzLines: { color: '#e0e0e0' }
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal
        },
        rightPriceScale: {
            borderColor: '#cccccc'
        },
        timeScale: {
            borderColor: '#cccccc',
            timeVisible: true
        }
    });

    lineSeries = chart.addLineSeries({
        color: '#49a2f6',
        lineWidth: 2,
        priceFormat: { type: 'price', precision: 0 }
    });

    loadChartData();

    window.addEventListener('resize', () => {
        chart.resize(container.clientWidth, container.clientHeight);
    });
}

async function loadChartData() {
    try {
        const response = await fetch(
            `${API_BASE_URL}/sentiments?gall_id=${currentGallery}&timeframe=${currentTimeframe}`
        );

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();
        renderChartData(result.data);
    } catch (error) {
        console.error('데이터 로드 실패:', error);
        returnErr();
    }
}

function renderChartData(data) {
    if (!data || data.length === 0) {
        returnErr();
        return;
    }

    const chartData = data.map((item) => {
        const [year, month, day] = item.date.split('-').map(Number);
        const dateObj = new Date(Date.UTC(year, month - 1, day));
        return {
            time: Math.floor(dateObj.getTime() / 1000),
            value: item.average_sentiment
        };
    });

    lineSeries.setData(chartData);
    chart.timeScale().fitContent();
    updateEmotionGif(chartData);
}

function returnErr() {
    const container = document.getElementById('chart-container');
    container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#888;font-size:16px;">데이터를 불러올 수 없습니다</div>';
    const gif = document.getElementById('emotionGif');
    gif.style.display = 'none';
}

function updateEmotionGif(chartData) {
    const gif = document.getElementById('emotionGif');
    if (!chartData || chartData.length === 0) {
        gif.style.display = 'none';
        return;
    }

    const lastPoint = chartData[chartData.length - 1];
    const lastValue = lastPoint.value;

    gif.src = lastValue >= 75 ? './happy.gif' : './sad.gif';
    gif.style.display = 'block';
    gif.style.width = '150px';
    gif.style.borderRadius = '50px';
    gif.style.pointerEvents = 'none';
    gif.style.position = 'absolute';
    gif.style.right = '60px';
    gif.style.bottom = '60px';
}

function resetZoom() {
    chart.timeScale().fitContent();
    const data = lineSeries.data();
    updateEmotionGif(data);
}

function changeTopic(text, gallId) {
    const topicEl = document.getElementById('topic-select');
    topicEl.childNodes[0].textContent = text + ' ';
    currentGallery = gallId;
    loadChartData();
}

document.querySelectorAll('.tf-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTimeframe = btn.dataset.tf;
        loadChartData();
    });
});

document.addEventListener('DOMContentLoaded', () => {
    initChart();
});
