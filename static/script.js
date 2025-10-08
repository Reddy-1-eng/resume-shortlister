class ResumeShortlister {
  constructor() {
    this.uploadedFiles = []
    this.isProcessing = false
    this.currentTab = "upload"
    this.minScore = 75
    this.candidates = [] // New property to store real candidate data

    this.initializeEventListeners()
    this.updateUI()
  }

  initializeEventListeners() {
    // Tab navigation
    document.querySelectorAll(".tab-button").forEach((button) => {
      button.addEventListener("click", (e) => {
        this.switchTab(e.target.dataset.tab)
      })
    })

    // File upload
    const fileInput = document.getElementById("file-input")
    const uploadArea = document.getElementById("upload-area")

    fileInput.addEventListener("change", (e) => {
      this.handleFileUpload(e.target.files)
    })

    // Drag and drop
    uploadArea.addEventListener("dragenter", this.handleDragEnter.bind(this))
    uploadArea.addEventListener("dragover", this.handleDragOver.bind(this))
    uploadArea.addEventListener("dragleave", this.handleDragLeave.bind(this))
    uploadArea.addEventListener("drop", this.handleDrop.bind(this))

    // Clear all files
    document.getElementById("clear-all-btn").addEventListener("click", () => {
      this.clearAllFiles()
    })

    // Configuration
    document.getElementById("job-role").addEventListener("change", () => {
      this.updateProcessButton()
    })

    document.getElementById("min-score").addEventListener("input", (e) => {
      this.minScore = Number.parseInt(e.target.value)
      this.updateResults()
    })

    // Process button
    document.getElementById("process-btn").addEventListener("click", () => {
      this.processResumes()
    })
    // Send Emails button
    document.getElementById("send-emails-btn").addEventListener("click", () => {
      this.sendEmailsToQualified()
    })
  }

  switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll(".tab-button").forEach((button) => {
      button.classList.remove("active")
    })
    document.querySelector(`[data-tab="${tabName}"]`).classList.add("active")

    // Update tab content
    document.querySelectorAll(".tab-content").forEach((content) => {
      content.classList.remove("active")
    })
    document.getElementById(`${tabName}-tab`).classList.add("active")

    this.currentTab = tabName
  }

  handleDragEnter(e) {
    e.preventDefault()
    e.stopPropagation()
    document.getElementById("upload-area").classList.add("drag-active")
  }

  handleDragOver(e) {
    e.preventDefault()
    e.stopPropagation()
  }

  handleDragLeave(e) {
    e.preventDefault()
    e.stopPropagation()
    if (!e.currentTarget.contains(e.relatedTarget)) {
      document.getElementById("upload-area").classList.remove("drag-active")
    }
  }

  handleDrop(e) {
    e.preventDefault()
    e.stopPropagation()
    document.getElementById("upload-area").classList.remove("drag-active")

    const files = Array.from(e.dataTransfer.files)
    this.handleFileUpload(files)
  }

  handleFileUpload(files) {
    const validFiles = Array.from(files).filter((file) => {
      const validTypes = [".pdf", ".doc", ".docx"]
      const fileExtension = "." + file.name.split(".").pop().toLowerCase()
      return validTypes.includes(fileExtension) && file.size <= 10 * 1024 * 1024 // 10MB limit
    })

    validFiles.forEach((file) => {
      const fileObj = {
        id: Date.now() + Math.random(),
        name: file.name,
        size: this.formatFileSize(file.size),
        status: "uploaded",
        score: null,
      }
      this.uploadedFiles.push(fileObj)
    })

    this.updateUI()
  }

  formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
  }

  removeFile(fileId) {
    this.uploadedFiles = this.uploadedFiles.filter((file) => file.id !== fileId)
    this.updateUI()
  }

  clearAllFiles() {
    this.uploadedFiles = []
    this.updateUI()
  }

  updateUI() {
    this.updateFileList()
    this.updateProcessButton()
    this.updateResults()
  }

  updateFileList() {
    const fileListContainer = document.getElementById("file-list-container")
    const fileList = document.getElementById("file-list")
    const fileCount = document.getElementById("file-count")

    if (this.uploadedFiles.length === 0) {
      fileListContainer.style.display = "none"
      return
    }

    fileListContainer.style.display = "block"
    fileCount.textContent = this.uploadedFiles.length

    fileList.innerHTML = this.uploadedFiles
      .map(
        (file) => `
            <div class="file-item">
                <div class="file-icon">
                    <i class="fas fa-file-text"></i>
                </div>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${file.size}</div>
                </div>
                <div class="file-status ${file.status}">
                    ${file.status === "completed" ? '<i class="fas fa-check-circle"></i>' : ""}
                    ${file.status.charAt(0).toUpperCase() + file.status.slice(1)}
                </div>
                <button class="remove-file-btn" onclick="app.removeFile(${file.id})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `,
      )
      .join("")
  }

  updateProcessButton() {
    const processBtn = document.getElementById("process-btn")
    const processCount = document.getElementById("process-count")
    const jobRole = document.getElementById("job-role").value

    processCount.textContent = this.uploadedFiles.length
    processBtn.disabled = this.uploadedFiles.length === 0 || !jobRole
  }

  async processResumes() {
    if (this.isProcessing) return

    this.isProcessing = true
    this.switchTab("results")

    // Show processing state
    document.getElementById("processing-state").style.display = "block"
    document.getElementById("results-state").style.display = "none"
    document.getElementById("empty-state").style.display = "none"

    // 1. Upload files to backend
    const filesToUpload = this.uploadedFiles.filter(f => f.status === "uploaded")
    const formData = new FormData()
    filesToUpload.forEach(f => {
      const fileInput = document.getElementById("file-input")
      for (let i = 0; i < fileInput.files.length; i++) {
        if (fileInput.files[i].name === f.name) {
          formData.append("files", fileInput.files[i])
        }
      }
    })
    let uploadedFilenames = []
    if (filesToUpload.length > 0) {
      try {
        const uploadResp = await fetch("/upload", { method: "POST", body: formData })
        const uploadData = await uploadResp.json()
        console.log("Upload response:", uploadData)
        if (!uploadData.success) {
          document.getElementById("processing-state").style.display = "none"
          document.getElementById("empty-state").style.display = "block"
          this.isProcessing = false
          alert(uploadData.error || "Upload failed")
          return
        }
        uploadedFilenames = uploadData.files
        // Map server filenames to uploadedFiles for later reference
        filesToUpload.forEach((f, idx) => { f.serverFilename = uploadedFilenames[idx] })
      } catch (err) {
        console.error("Upload error:", err)
        document.getElementById("processing-state").style.display = "none"
        document.getElementById("empty-state").style.display = "block"
        this.isProcessing = false
        alert("Upload failed: " + err)
        return
      }
    } else {
      uploadedFilenames = this.uploadedFiles.map(f => f.serverFilename || f.name)
    }

    // 2. Call /process for real resume analysis
    const jobRole = document.getElementById("job-role").value
    const threshold = this.minScore
    try {
      const processResp = await fetch("/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_role: jobRole, threshold, files: uploadedFilenames })
      })
      const processData = await processResp.json()
      console.log("Process response:", processData)
      if (!processData.success) {
        document.getElementById("processing-state").style.display = "none"
        document.getElementById("empty-state").style.display = "block"
        this.isProcessing = false
        alert(processData.error || "Processing failed")
        return
      }
      this.candidates = processData.candidates || []
      this.isProcessing = false
      document.getElementById("processing-state").style.display = "none"
      document.getElementById("results-state").style.display = "block"
      document.getElementById("empty-state").style.display = "none"
      this.updateResults()
    } catch (err) {
      console.error("Process error:", err)
      document.getElementById("processing-state").style.display = "none"
      document.getElementById("empty-state").style.display = "block"
      this.isProcessing = false
      alert("Processing failed: " + err)
      return
    }
  }

  updateResults() {
    // Use real candidate data if available
    const candidates = this.candidates || []
    if (candidates.length === 0) {
      document.getElementById("empty-state").style.display = "block"
      document.getElementById("results-state").style.display = "none"
      return
    }
    // Update stats
    const totalResumes = candidates.length
    const qualifiedCount = candidates.filter((c) => c.overall >= this.minScore).length
    const averageScore = candidates.length > 0 ? Math.round(candidates.reduce((sum, c) => sum + c.overall, 0) / candidates.length) : 0
    document.getElementById("total-resumes").textContent = totalResumes
    document.getElementById("qualified-count").textContent = qualifiedCount
    document.getElementById("average-score").textContent = averageScore
    // Update results list
    const resultsList = document.getElementById("results-list")
    const sortedCandidates = [...candidates].sort((a, b) => b.overall - a.overall)
    resultsList.innerHTML = sortedCandidates
      .map((c) => {
        const isQualified = c.overall >= this.minScore
        return `
                <div class="result-item">
                    <div class="result-file-icon">
                        <i class="fas fa-file-text"></i>
                    </div>
                    <div class="result-info">
                        <div class="result-name">${c.name}</div>
                        <div class="result-size">${c.email}</div>
                    </div>
                    <div class="result-score">
                        <div class="score-number ${isQualified ? "qualified" : "not-qualified"}">
                            ${c.overall}
                        </div>
                        <div class="score-label">Score</div>
                    </div>
                    <div class="result-status ${isQualified ? "qualified" : "not-qualified"}">
                        ${isQualified ? "Qualified" : "Not Qualified"}
                    </div>
                </div>
            `
      })
      .join("")
  }

  async sendEmailsToQualified() {
    const candidates = this.candidates || []
    const qualified = candidates.filter((c) => c.overall >= this.minScore && c.email && c.email !== "N/A" && c.email.includes("@"))
    if (qualified.length === 0) {
      document.getElementById("send-emails-status").textContent = "No qualified candidates to email."
      return
    }
    document.getElementById("send-emails-status").textContent = "Sending emails..."
    try {
      const response = await fetch("/send-emails", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidates: qualified, threshold: this.minScore, job_role: document.getElementById("job-role").value })
      })
      const result = await response.json()
      console.log("Send emails response:", result)
      if (result.success) {
        document.getElementById("send-emails-status").textContent = result.message
      } else {
        document.getElementById("send-emails-status").textContent = result.error || "Failed to send emails."
      }
    } catch (err) {
      console.error("Send emails error:", err)
      document.getElementById("send-emails-status").textContent = "Error sending emails."
    }
  }
}

// Initialize the application
const app = new ResumeShortlister()

// Make app globally available for onclick handlers
window.app = app
