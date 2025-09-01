console.log('📊 Dashboard.js carregando...');

// ✅ VARIÁVEL GLOBAL PARA CONTROLAR INICIALIZAÇÃO
let dashboardInitialized = false;

// ✅ FUNÇÃO ÚNICA DE INICIALIZAÇÃO
function initializeDashboard() {
    console.log('🎯 Tentando inicializar dashboard...');
    
    // ✅ PREVENIR MÚLTIPLAS EXECUÇÕES
    if (dashboardInitialized) {
        console.warn('⚠️ Dashboard já foi inicializado, ignorando...');
        return;
    }
    
    // Verificar dependências
    if (typeof Chart === 'undefined') {
        console.error('❌ Chart.js não carregado!');
        return;
    }
    
    if (!window.dashboardData) {
        console.error('❌ dashboardData não disponível!');
        return;
    }
    
    // ✅ MARCAR COMO INICIALIZADO
    dashboardInitialized = true;
    
    console.log('🔍 DEBUG - Dados recebidos:', {
        dashboardData: window.dashboardData,
        chartDefined: typeof Chart !== 'undefined'
    });
    
    // ✅ CONVERTER DADOS SE NECESSÁRIO
    if (typeof window.dashboardData.timeline_labels === 'string') {
        console.log('🔄 Convertendo timeline_labels...');
        window.dashboardData.timeline_labels = JSON.parse(window.dashboardData.timeline_labels);
    }
    
    if (typeof window.dashboardData.timeline_data === 'string') {
        console.log('🔄 Convertendo timeline_data...');
        window.dashboardData.timeline_data = JSON.parse(window.dashboardData.timeline_data);
    }
    
    if (typeof window.dashboardData.confidence_distribution === 'string') {
        console.log('🔄 Convertendo confidence_distribution...');
        window.dashboardData.confidence_distribution = JSON.parse(window.dashboardData.confidence_distribution);
    }
    
    console.log('📊 Dados após conversão:', window.dashboardData);
    
    // ✅ CRIAR DASHBOARD MANAGER APENAS UMA VEZ
    console.log('✅ Criando DashboardManager único...');
    window.dashboardManager = new DashboardManager();
}

// ✅ AGUARDAR DOM CARREGAR (APENAS UMA VEZ)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
    // DOM já carregado, inicializar após pequeno delay para garantir que dados estão prontos
    setTimeout(initializeDashboard, 100);
}

class DashboardManager {
    constructor() {
        console.log('📊 DashboardManager construtor iniciado');
        
        this.charts = {};
        this.colors = {
            productive: '#10b981',
            unproductive: '#ef4444',
            neutral: '#f59e0b',
            primary: '#667eea'
        };
        
        // ✅ INICIALIZAR IMEDIATAMENTE
        this.init();
    }
    
    init() {
        console.log('🚀 Inicializando dashboard...');
        
        // Verificar elementos
        const elements = this.getCanvasElements();
        
        console.log('📋 Elementos encontrados:', elements);
        
        if (elements.allFound) {
            this.createAllCharts();
            console.log('✅ Dashboard inicializado com sucesso!');
        } else {
            console.error('❌ Nem todos os elementos canvas foram encontrados');
        }
    }
    
    getCanvasElements() {
        const categoryChart = document.getElementById('categoryChart');
        const timelineChart = document.getElementById('timelineChart');
        const confidenceChart = document.getElementById('confidenceChart');
        
        return {
            category: categoryChart,
            timeline: timelineChart,
            confidence: confidenceChart,
            allFound: !!(categoryChart && timelineChart && confidenceChart)
        };
    }
    
    createAllCharts() {
        console.log('📊 Criando todos os gráficos...');
        
        try {
            this.createCategoryChart();
            this.createTimelineChart();
            this.createConfidenceChart();
            console.log('✅ Todos os gráficos criados com sucesso');
        } catch (error) {
            console.error('❌ Erro ao criar gráficos:', error);
        }
    }
    
    createCategoryChart() {
        const ctx = document.getElementById('categoryChart');
        if (!ctx) {
            console.error('❌ categoryChart não encontrado');
            return;
        }
        
        console.log('📈 Criando gráfico de categoria...');
        
        // ✅ GARANTIR QUE NÃO EXISTE CHART ANTERIOR
        if (this.charts.category) {
            this.charts.category.destroy();
            this.charts.category = null;
        }
        
        const stats = window.dashboardData?.stats || {};
        const productiveCount = stats.productive_emails || 0;
        const unproductiveCount = stats.unproductive_emails || 0;
        
        console.log('📊 Dados categoria:', { productiveCount, unproductiveCount });
        
        this.charts.category = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Produtivo', 'Não Produtivo'],
                datasets: [{
                    data: [productiveCount, unproductiveCount],
                    backgroundColor: [this.colors.productive, this.colors.unproductive],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { padding: 20, font: { size: 12 } }
                    }
                }
            }
        });
        
        console.log('✅ Gráfico de categoria criado');
    }
    
    createTimelineChart() {
        const ctx = document.getElementById('timelineChart');
        if (!ctx) {
            console.error('❌ timelineChart não encontrado');
            return;
        }
        
        console.log('📈 Criando gráfico de timeline...');
        
        // ✅ GARANTIR QUE NÃO EXISTE CHART ANTERIOR
        if (this.charts.timeline) {
            this.charts.timeline.destroy();
            this.charts.timeline = null;
        }
        
        const labels = window.dashboardData?.timeline_labels || [];
        const data = window.dashboardData?.timeline_data || [];
        
        console.log('📊 Dados timeline:', { labels, data });
        
        this.charts.timeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Classificações',
                    data: data,
                    borderColor: this.colors.primary,
                    backgroundColor: this.colors.primary + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } }
                }
            }
        });
        
        console.log('✅ Gráfico de timeline criado');
    }
    
    createConfidenceChart() {
        const ctx = document.getElementById('confidenceChart');
        if (!ctx) {
            console.error('❌ confidenceChart não encontrado');
            return;
        }
        
        console.log('📈 Criando gráfico de confiança...');
        
        // ✅ GARANTIR QUE NÃO EXISTE CHART ANTERIOR
        if (this.charts.confidence) {
            this.charts.confidence.destroy();
            this.charts.confidence = null;
        }
        
        const data = window.dashboardData?.confidence_distribution || [0, 0, 0, 0, 0];
        
        console.log('📊 Dados confiança:', data);
        
        this.charts.confidence = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%'],
                datasets: [{
                    label: 'Classificações',
                    data: data,
                    backgroundColor: ['#ef4444', '#f59e0b', '#eab308', '#22c55e', '#10b981'],
                    borderWidth: 1,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } }
                }
            }
        });
        
        console.log('✅ Gráfico de confiança criado');
    }
    
    destroy() {
        console.log('🗑️ Destruindo DashboardManager...');
        
        Object.keys(this.charts).forEach(key => {
            if (this.charts[key]) {
                console.log(`🗑️ Destruindo gráfico: ${key}`);
                this.charts[key].destroy();
                this.charts[key] = null;
            }
        });
        
        this.charts = {};
        
        // ✅ RESETAR FLAG DE INICIALIZAÇÃO
        dashboardInitialized = false;
    }
}

// ✅ DISPONIBILIZAR GLOBALMENTE
window.DashboardManager = DashboardManager;

console.log('✅ Dashboard.js carregado');