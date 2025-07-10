/**
 * TraceGPT - Utility functions for trace visualization
 */

class TraceVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Container element not found');
            return;
        }
    }

    /**
     * Renders a trace timeline with steps
     * @param {Array} steps - Array of trace steps
     */
    renderTimeline(steps) {
        if (!steps || !steps.length) {
            this.container.innerHTML = '<div class="alert alert-warning">No steps to display</div>';
            return;
        }

        // Clear the container
        this.container.innerHTML = '';
        
        // Create timeline container
        const timeline = document.createElement('div');
        timeline.className = 'trace-timeline';
        
        // Add each step
        steps.forEach((step, index) => {
            const stepEl = this.createStepElement(step, index);
            timeline.appendChild(stepEl);
        });
        
        // Append to container
        this.container.appendChild(timeline);
    }
    
    /**
     * Creates a step element for the timeline
     * @param {Object} step - Step data
     * @param {Number} index - Step index
     */
    createStepElement(step, index) {
        const stepEl = document.createElement('div');
        stepEl.className = `trace-step trace-type-${step.type}`;
        stepEl.dataset.stepId = step.id || index;
        
        // Format duration
        const duration = step.runtime ? `${step.runtime.toFixed(2)}s` : '';
        
        // Build step header
        const header = document.createElement('div');
        header.className = 'd-flex justify-content-between align-items-center';
        header.innerHTML = `
            <h5 class="mb-1">${step.name || 'Unknown Step'}</h5>
            <span class="badge bg-secondary">${duration}</span>
        `;
        
        // Build step content
        const content = document.createElement('div');
        content.className = 'mt-2';
        content.innerHTML = `
            <p class="text-muted small mb-2">
                <i class="bi bi-tag"></i> ${step.type || 'unknown'} 
                ${step.timestamp ? `<span class="ms-2"><i class="bi bi-clock"></i> ${new Date(step.timestamp).toLocaleTimeString()}</span>` : ''}
            </p>
        `;
        
        // Add expandable details if we have input/output data
        if (step.input || step.output) {
            const details = document.createElement('details');
            details.className = 'mt-2';
            
            const summary = document.createElement('summary');
            summary.className = 'text-primary cursor-pointer';
            summary.textContent = 'View Details';
            
            const detailContent = document.createElement('div');
            detailContent.className = 'mt-2 p-2 border rounded bg-light';
            
            // Add input data if available
            if (step.input) {
                const inputData = document.createElement('div');
                inputData.className = 'mb-2';
                inputData.innerHTML = `
                    <h6 class="text-muted">Input:</h6>
                    <pre class="small">${JSON.stringify(step.input, null, 2)}</pre>
                `;
                detailContent.appendChild(inputData);
            }
            
            // Add output data if available
            if (step.output) {
                const outputData = document.createElement('div');
                outputData.innerHTML = `
                    <h6 class="text-muted">Output:</h6>
                    <pre class="small">${JSON.stringify(step.output, null, 2)}</pre>
                `;
                detailContent.appendChild(outputData);
            }
            
            details.appendChild(summary);
            details.appendChild(detailContent);
            content.appendChild(details);
        }
        
        // Assemble step element
        stepEl.appendChild(header);
        stepEl.appendChild(content);
        
        return stepEl;
    }
    
    /**
     * Renders a simple summary of trace metrics
     * @param {Object} metrics - Trace metrics
     */
    renderMetrics(metrics) {
        if (!metrics) return;
        
        const metricsEl = document.createElement('div');
        metricsEl.className = 'alert alert-info';
        
        const items = [];
        
        if (metrics.totalRuntime) {
            items.push(`<strong>Total Runtime:</strong> ${metrics.totalRuntime.toFixed(2)}s`);
        }
        
        if (metrics.stepCount) {
            items.push(`<strong>Steps:</strong> ${metrics.stepCount}`);
        }
        
        if (metrics.status) {
            const statusClass = metrics.status === 'success' ? 'text-success' : 'text-danger';
            items.push(`<strong>Status:</strong> <span class="${statusClass}">${metrics.status}</span>`);
        }
        
        metricsEl.innerHTML = items.join(' | ');
        
        // Insert at the top of the container
        if (this.container.firstChild) {
            this.container.insertBefore(metricsEl, this.container.firstChild);
        } else {
            this.container.appendChild(metricsEl);
        }
    }
}

// Export for use in other files
window.TraceVisualizer = TraceVisualizer; 