/**
 * AutoU Email Classifier - Upload JavaScript CORRIGIDO
 * Versão que processa corretamente as respostas da API
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Upload.js iniciado - Versão CORRIGIDA para classificação');

    // Elementos do DOM
    const form = document.getElementById('classificationForm');
    const classifyBtn = document.getElementById('classifyBtn');
    const emailSubject = document.getElementById('emailSubject');
    const emailContent = document.getElementById('emailContent');
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const resultsCard = document.getElementById('resultsCard');
    const resultsContent = document.getElementById('resultsContent');

    // Event listeners
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    if (uploadZone && fileInput) {
        uploadZone.addEventListener('click', () => fileInput.click());
        uploadZone.addEventListener('dragover', handleDragOver);
        uploadZone.addEventListener('drop', handleFileDrop);
        fileInput.addEventListener('change', handleFileSelect);
    }

    function handleFormSubmit(e) {
        e.preventDefault();
        
        const subject = emailSubject ? emailSubject.value.trim() : '';
        const content = emailContent ? emailContent.value.trim() : '';

        if (!content) {
            showAlert('Por favor, insira o conteúdo do email.', 'danger');
            emailContent?.focus();
            return;
        }

        classifyEmail(subject, content);
    }

    function handleDragOver(e) {
        e.preventDefault();
        uploadZone?.classList.add('border-primary');
    }

    function handleFileDrop(e) {
        e.preventDefault();
        uploadZone?.classList.remove('border-primary');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            processFile(files[0]);
        }
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            processFile(files[0]);
        }
    }

    function processFile(file) {
        if (file.size > 5 * 1024 * 1024) {
            showAlert('Arquivo muito grande. Máximo 5MB.', 'danger');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            const subject = file.name.replace(/\.[^/.]+$/, "");
            
            if (emailSubject) emailSubject.value = subject;
            if (emailContent) emailContent.value = content;
            
            showAlert(`Arquivo "${file.name}" carregado com sucesso!`, 'success');
        };
        
        reader.readAsText(file);
    }

    function classifyEmail(subject, content) {
        console.log('📧 Iniciando classificação...', { 
            subject: subject, 
            contentLength: content.length,
            contentPreview: content.substring(0, 100) + '...'
        });
        
        setLoadingState(true);
        hideResults();

        const data = {
            subject: subject || 'Email sem assunto',
            content: content
        };

        // Fazer requisição AJAX
        fetch('/upload-ajax/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            console.log('📡 Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📋 Response data completa:', data);
            setLoadingState(false);
            
            if (data.success) {
                displayResults(data);
                showAlert('Email classificado com sucesso!', 'success');
            } else {
                console.error('❌ Erro na resposta:', data.error);
                showAlert(`Erro: ${data.error || 'Erro desconhecido'}`, 'danger');
            }
        })
        .catch(error => {
            console.error('❌ Erro na requisição:', error);
            setLoadingState(false);
            showAlert('Erro ao processar classificação. Verifique a conexão.', 'danger');
        });
    }

    function displayResults(data) {
        if (!resultsCard || !resultsContent) {
            console.error('❌ Elementos de resultado não encontrados');
            return;
        }

        console.log('🎯 Processando resultados:', data);

        // Extrair classificação - testar várias possibilidades
        const possibleClassifications = [
            data.classification,
            data.classification_result,
            data.category,
            data.result
        ];
        
        let classification = 'unknown';
        for (const possible of possibleClassifications) {
            if (possible && possible !== 'unknown') {
                classification = possible.toString().toLowerCase();
                break;
            }
        }

        console.log('🔍 Classificação detectada:', classification);

        // Extrair outros dados
        const confidence = parseFloat(data.confidence_score || data.confidence || 0);
        const confidencePercent = Math.round(confidence * 100);
        const reasoning = data.reasoning || data.message || 'Análise realizada com sucesso';
        const subject = data.subject || emailSubject?.value || 'Sem assunto';
        const recommendedResponse = data.recommended_response || '';
        
        // Determinar classificação final e recomendações
        let classificationText, classificationIcon, badgeClass, defaultRecommendation;
        
        switch(classification) {
            case 'productive':
            case 'legitimate':
            case 'important':
            case 'work':
            case 'business':
                classificationText = 'PRODUTIVO';
                classificationIcon = '✅';
                badgeClass = 'productive';
                defaultRecommendation = '✅ RESPONDER COM PRIORIDADE: Este email é importante para sua produtividade. Recomendo ação imediata.';
                break;
                
            case 'unproductive':
            case 'spam':
            case 'phishing':
            case 'junk':
            case 'irrelevant':
                classificationText = 'IMPRODUTIVO';
                classificationIcon = '❌';
                badgeClass = 'unproductive';
                defaultRecommendation = '❌ IGNORAR OU DELETAR: Este email não contribui para sua produtividade. Pode ser ignorado.';
                break;
                
            case 'neutral':
            case 'moderate':
            case 'uncertain':
                classificationText = 'NEUTRO';
                classificationIcon = '⚠️';
                badgeClass = 'neutral';
                defaultRecommendation = '⚠️ AVALIAR CONFORME NECESSÁRIO: Email de importância moderada. Responda quando conveniente.';
                break;
                
            default:
                // Análise de fallback baseada no conteúdo
                const contentLower = (emailContent?.value || '').toLowerCase();
                const subjectLower = subject.toLowerCase();
                
                const productiveKeywords = ['reunião', 'meeting', 'projeto', 'project', 'trabalho', 'deadline', 'importante', 'urgent'];
                const unproductiveKeywords = ['spam', 'promoção', 'desconto', 'oferta', 'free', 'winner', 'click here'];
                
                const hasProductive = productiveKeywords.some(keyword => 
                    contentLower.includes(keyword) || subjectLower.includes(keyword)
                );
                const hasUnproductive = unproductiveKeywords.some(keyword => 
                    contentLower.includes(keyword) || subjectLower.includes(keyword)
                );
                
                if (hasProductive && !hasUnproductive) {
                    classificationText = 'PRODUTIVO';
                    classificationIcon = '✅';
                    badgeClass = 'productive';
                    defaultRecommendation = '✅ RESPONDER COM PRIORIDADE: Email identificado como produtivo pela análise de conteúdo.';
                } else if (hasUnproductive && !hasProductive) {
                    classificationText = 'IMPRODUTIVO';
                    classificationIcon = '❌';
                    badgeClass = 'unproductive';
                    defaultRecommendation = '❌ IGNORAR OU DELETAR: Email identificado como não produtivo pela análise de conteúdo.';
                } else {
                    classificationText = 'NEUTRO';
                    classificationIcon = '⚠️';
                    badgeClass = 'neutral';
                    defaultRecommendation = '⚠️ AVALIAR MANUALMENTE: Não foi possível determinar a produtividade automaticamente.';
                }
        }

        // Usar recomendação da API ou fallback
        const finalRecommendation = recommendedResponse || defaultRecommendation;

        console.log('📊 Resultado final:', {
            classification: classificationText,
            confidence: confidencePercent,
            recommendation: finalRecommendation
        });

        // Determinar cor da barra de confiança
        let confidenceBarClass = 'bg-danger';
        if (confidencePercent >= 80) confidenceBarClass = 'bg-success';
        else if (confidencePercent >= 60) confidenceBarClass = 'bg-warning';

        // Gerar HTML do resultado
        const resultHTML = `
            <div class="row g-4">
                <!-- Classificação Principal -->
                <div class="col-12">
                    <div class="text-center mb-4">
                        <div class="classification-badge ${badgeClass} mx-auto mb-3" 
                             style="padding: 1.5rem 2.5rem; border-radius: 30px; display: inline-block; 
                                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                            <span style="font-size: 2rem; margin-right: 0.75rem;">${classificationIcon}</span>
                            <span style="font-size: 1.5rem; font-weight: 800; text-transform: uppercase;">${classificationText}</span>
                        </div>
                        <div class="confidence-section">
                            <h6 class="mb-3 fw-bold">Confiança da IA: ${confidencePercent}%</h6>
                            <div class="progress" style="height: 15px; border-radius: 8px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
                                <div class="progress-bar ${confidenceBarClass}" 
                                     style="width: ${confidencePercent}%; transition: width 1s ease-in-out;
                                            background: linear-gradient(45deg, ${confidenceBarClass.replace('bg-', '')} 0%, ${confidenceBarClass.replace('bg-', '')} 100%);">
                                    <span class="fw-bold">${confidencePercent}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Informações do Email -->
                <div class="col-md-6">
                    <div class="info-card p-4 rounded h-100" style="background: var(--bg-tertiary); border-left: 4px solid var(--accent-primary);">
                        <h6 class="fw-bold mb-3 text-primary">
                            <i class="fas fa-envelope me-2"></i>Informações do Email
                        </h6>
                        <div class="info-item mb-3">
                            <strong class="text-primary">Assunto:</strong>
                            <p class="mb-1 text-secondary mt-1">"${subject}"</p>
                        </div>
                        <div class="info-item mb-3">
                            <strong class="text-primary">ID:</strong>
                            <span class="text-muted">#${data.email_id || 'AUTO'}</span>
                        </div>
                        ${data.processing_time ? `
                            <div class="info-item">
                                <strong class="text-primary">Tempo de processamento:</strong>
                                <span class="text-muted">${data.processing_time}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <!-- Resposta Recomendada -->
                <div class="col-md-6">
                    <div class="info-card p-4 rounded h-100" style="background: var(--bg-tertiary); border-left: 4px solid var(--accent-success);">
                        <h6 class="fw-bold mb-3 text-success">
                            <i class="fas fa-lightbulb me-2"></i>Resposta Recomendada
                        </h6>
                        <div class="recommendation-content" style="line-height: 1.6;">
                            <p class="mb-0 text-secondary fw-medium">
                                ${finalRecommendation}
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Justificativa da IA -->
                <div class="col-12">
                    <div class="reasoning-card p-4 rounded" 
                         style="background: rgba(139, 92, 246, 0.1); border-left: 4px solid var(--accent-primary); border: 1px solid rgba(139, 92, 246, 0.2);">
                        <h6 class="fw-bold mb-3">
                            <i class="fas fa-brain me-2"></i>Justificativa da IA
                        </h6>
                        <blockquote class="mb-0 fst-italic text-secondary" style="line-height: 1.7; font-size: 1.05rem;">
                            "${reasoning}"
                        </blockquote>
                    </div>
                </div>
                
                <!-- Ações -->
                <div class="col-12">
                    <div class="d-flex gap-3 flex-wrap justify-content-center mt-3">
                        <button class="btn btn-primary btn-lg" onclick="resetForm()">
                            <i class="fas fa-plus me-2"></i>Analisar Outro Email
                        </button>
                        <a href="/results/" class="btn btn-outline-primary btn-lg">
                            <i class="fas fa-history me-2"></i>Ver Histórico
                        </a>
                        <a href="/dashboard/" class="btn btn-outline-success btn-lg">
                            <i class="fas fa-chart-line me-2"></i>Dashboard
                        </a>
                    </div>
                </div>
            </div>
        `;

        resultsContent.innerHTML = resultHTML;
        resultsCard.classList.remove('d-none');
        
        // Atualizar header do card
        const cardHeader = resultsCard.querySelector('.card-header');
        if (cardHeader) {
            const headerColors = {
                'productive': 'bg-success',
                'unproductive': 'bg-danger',
                'neutral': 'bg-warning'
            };
            
            cardHeader.className = `card-header ${headerColors[badgeClass]} text-white`;
            cardHeader.innerHTML = `
                <h5 class="mb-0 fw-bold">
                    ${classificationIcon} Resultado: ${classificationText}
                </h5>
            `;
        }
        
        // Scroll suave para resultado
        setTimeout(() => {
            resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 200);
    }

    function setLoadingState(loading) {
        if (!classifyBtn) return;

        const btnText = classifyBtn.querySelector('.btn-text');
        const spinner = classifyBtn.querySelector('#loadingSpinner');

        if (loading) {
            classifyBtn.disabled = true;
            if (btnText) btnText.textContent = 'Analisando...';
            if (spinner) spinner.classList.remove('d-none');
        } else {
            classifyBtn.disabled = false;
            if (btnText) btnText.textContent = 'Analisar';
            if (spinner) spinner.classList.add('d-none');
        }
    }

    function hideResults() {
        if (resultsCard) {
            resultsCard.classList.add('d-none');
        }
    }

    function showAlert(message, type) {
        // Remover alertas anteriores
        document.querySelectorAll('.temp-alert').forEach(alert => alert.remove());

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show temp-alert mt-3`;
        alertDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                <span>${message}</span>
            </div>
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        // Inserir antes do formulário
        if (form && form.parentNode) {
            form.parentNode.insertBefore(alertDiv, form);
        }
        
        // Auto remove após 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    function getCsrfToken() {
        // Procurar token CSRF no formulário
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) return csrfInput.value;

        // Procurar em meta tag
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) return csrfMeta.getAttribute('content');

        // Procurar em cookies
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        return '';
    }

    // Função global para reset
    window.resetForm = function() {
        if (form) {
            form.reset();
            form.classList.remove('was-validated');
        }
        hideResults();
        document.querySelectorAll('.temp-alert').forEach(alert => alert.remove());
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    console.log('✅ Upload.js carregado - VERSÃO CORRIGIDA para classificação produtivo/improdutivo');
});
