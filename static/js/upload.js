document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('classificationForm');
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const classifyBtn = document.getElementById('classifyBtn');
    const resultsCard = document.getElementById('resultsCard');

    // Form submission
    form.addEventListener('submit', handleFormSubmit);

    // File upload functionality
    uploadZone.addEventListener('click', () => fileInput.click());
    uploadZone.addEventListener('dragover', handleDragOver);
    uploadZone.addEventListener('drop', handleFileDrop);
    fileInput.addEventListener('change', handleFileSelect);

    function handleFormSubmit(e) {
        e.preventDefault();
        
        if (!form.checkValidity()) {
            e.stopPropagation();
            form.classList.add('was-validated');
            return;
        }

        classifyEmail();
    }

    function handleDragOver(e) {
        e.preventDefault();
        uploadZone.classList.add('border-primary', 'bg-light');
    }

    function handleFileDrop(e) {
        e.preventDefault();
        uploadZone.classList.remove('border-primary', 'bg-light');
        
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
        if (file.size > 5 * 1024 * 1024) { // 5MB limit
            showAlert('Arquivo muito grande. Máximo 5MB.', 'danger');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            
            // Extract subject from filename if possible
            const subject = file.name.replace(/\.[^/.]+$/, ""); // Remove extension
            
            document.getElementById('emailSubject').value = subject;
            document.getElementById('emailContent').value = content;
            
            showAlert(`Arquivo "${file.name}" carregado com sucesso!`, 'success');
        };
        
        reader.readAsText(file);
    }

    function classifyEmail() {
        const subject = document.getElementById('emailSubject').value;
        const content = document.getElementById('emailContent').value;

        // Show loading state
        setLoadingState(true);

        const data = {
            subject: subject,
            content: content
        };

        fetch('/api/classifier/classifications/classify_no_db/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            setLoadingState(false);
            
            if (data.error) {
                showAlert(`Erro: ${data.error}`, 'danger');
                return;
            }
            
            displayResults(data);
        })
        .catch(error => {
            setLoadingState(false);
            console.error('Erro:', error);
            showAlert('Erro ao processar classificação. Tente novamente.', 'danger');
        });
    }

    function displayResults(result) {
        const resultsContent = document.getElementById('resultsContent');
        
        const confidencePercent = Math.round((result.confidence_score || 0) * 100);
        const classificationClass = result.classification_result === 'productive' ? 'success' : 'danger';
        const classificationIcon = result.classification_result === 'productive' ? 'check-circle' : 'times-circle';
        const classificationText = result.classification_result === 'productive' ? 'Produtivo' : 'Não Produtivo';

        resultsContent.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6 class="fw-bold mb-3">📧 Informações do Email</h6>
                    <p><strong>Assunto:</strong> ${result.email?.subject || 'N/A'}</p>
                    <p><strong>Conteúdo:</strong></p>
                    <div class="bg-light p-3 rounded" style="max-height: 150px; overflow-y: auto;">
                        <small>${(result.email?.content || '').substring(0, 300)}${(result.email?.content || '').length > 300 ? '...' : ''}</small>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6 class="fw-bold mb-3">🤖 Resultado da IA</h6>
                    
                    <div class="alert alert-${classificationClass} d-flex align-items-center">
                        <i class="fas fa-${classificationIcon} me-2"></i>
                        <strong>Classificação: ${classificationText}</strong>
                    </div>
                    
                    <div class="mb-3">
                        <label class="fw-semibold mb-2">Confiança da Classificação</label>
                        <div class="progress" style="height: 25px;">
                            <div class="progress-bar bg-${classificationClass}" 
                                 style="width: ${confidencePercent}%">
                                ${confidencePercent}%
                            </div>
                        </div>
                    </div>
                    
                    ${result.reasoning ? `
                        <div>
                            <label class="fw-semibold mb-2">Justificativa da IA</label>
                            <div class="bg-light p-3 rounded">
                                <small>${result.reasoning}</small>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <div class="d-flex gap-2">
                        <button class="btn btn-primary" onclick="classifyAnother()">
                            <i class="fas fa-plus me-2"></i>Classificar Outro Email
                        </button>
                        <a href="/results/" class="btn btn-outline-primary">
                            <i class="fas fa-list me-2"></i>Ver Todos os Resultados
                        </a>
                        <a href="/dashboard/test/" class="btn btn-outline-secondary">
                            <i class="fas fa-chart-bar me-2"></i>Dashboard
                        </a>
                    </div>
                </div>
            </div>
        `;

        resultsCard.classList.remove('d-none');
        resultsCard.scrollIntoView({ behavior: 'smooth' });
    }

    function setLoadingState(loading) {
        const btnText = classifyBtn.querySelector('.btn-text');
        const spinner = document.getElementById('loadingSpinner');

        if (loading) {
            btnText.textContent = 'Classificando...';
            spinner.classList.remove('d-none');
            classifyBtn.disabled = true;
        } else {
            btnText.textContent = 'Classificar Email';
            spinner.classList.add('d-none');
            classifyBtn.disabled = false;
        }
    }

    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        form.parentNode.insertBefore(alertDiv, resultsCard);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    // Global function for "classify another" button
    window.classifyAnother = function() {
        form.reset();
        form.classList.remove('was-validated');
        resultsCard.classList.add('d-none');
        document.querySelector('.alert')?.remove();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };
});