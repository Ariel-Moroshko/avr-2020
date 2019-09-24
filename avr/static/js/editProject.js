class Observable {
    constructor() {
        this.observers = [];
    }
    subscribe(fn) {
        this.observers.push(fn);
    }

    unSubscribe(fn) {
        this.observers = this.observers.filter(observer => observer !== fn);
    }

    notify(data) {
        this.observers.forEach(observer => observer(data));
    }
}

class StudentsTable extends Observable{
    constructor(tableDom) {
        super();
        this.table = tableDom;
        this.table.on("click-row.bs.table", this.handleClick.bind(this));
        this.table.on('load-success.bs.table', this.handleLoad.bind(this));
        this.btnSave = $("#btnSaveStudentChanges");
        this.btnSave.on("click", this.handleSave.bind(this));
        this.selected = [];
        this.target = null; 
    }

    open(target, selected) {
        this.selected = [...selected];
        this.target = target;
        this.table.bootstrapTable('refresh');
        $('#addStudentsModal').modal("show");
    }

    highlight(element) {
        element.toggleClass("student-selected");
    }

    unHighlight(element) {
        element.toggleClass("student-selected");
    }

    select(student) {
        this.selected.push(student);
    }

    unSelect(id) {
        this.selected = this.selected.filter(student => student.id !== id);
    }

    handleClick(e, row, element) {
        let studentId = row.id;
        if (this.selected.filter(student => student.id === studentId).length > 0) {
            this.unSelect(studentId);
            this.unHighlight(element);
        }
        else {
            let profilePicSrc = $(row.profilePic).attr("src");
            this.select({
                id: studentId,
                firstNameHeb: row.firstNameHeb,
                lastNameHeb: row.lastNameHeb,
                firstNameEng: row.firstNameEng,
                lastNameEng: row.lastNameEng,
                email: row.email,
                profilePic: profilePicSrc,
                studentId: row.studentId
            });
            this.highlight(element);
        }
    }

    handleLoad(data) {
        // highlight all selected students
        var thisTable = this;
        this.table.find('tbody tr').each(function () {
            let currRowStudentId = $(this).data("uniqueid");
            let currentRow = this;
            
            if (thisTable.selected.filter(student => student.id === currRowStudentId).length > 0) {
                $(currentRow).addClass('student-selected');
            }
        });		
    }

    handleSave() {
        let data = {
            target: this.target,
            selected: this.selected
        }
        this.notify(data);
    }
}

class StudentsList {
    constructor(target, containerDom) {       
        this.addTable = null;
        this.target = target;
        this.students = [];
        this.container = containerDom;
    }
    
    setAddTable(addTable) {
        this.addTable = addTable;
        this.addTable.subscribe(this.handleSaveBtn.bind(this));
    }

    setStudents(students) {
        this.students = [...students];
    }

    handleSaveBtn(data) {
        if (data.target === this.target) {
            this.setStudents(data.selected);
            this.render();
        }
    }

    setNewStudents(students) {
        this.setStudents(students);
        this.render();
    }

    removeStudent(id) {
        this.students = this.students.filter(student => student.id !== id);
    }

    handleRemoveStudent(element) {
        let btnRemove = element.target;
        let studentId = $(btnRemove).data("id");
        let studentCard = $(btnRemove).closest("div[name='studentCard']");
        this.removeStudent(studentId);
        
        studentCard.fadeOut(300,function(){
            studentCard.remove();
        })
    }

    handleCourseNumChange(element) {
        let studentId = $(element.target).closest("select").data("student-id");
        let studentChanged = this.students.find(student => (student.id) === studentId);
        let selectedCourseId = parseInt($(element.target).val());
        studentChanged.courseId = selectedCourseId;
    }

    render() {
        this.container.empty();	
        let htmlContent = "";
        let cardSize = this.target === "addProject" ? "col-12 col-md-8 mx-auto" : "col-sm-6";
        htmlContent += `<div class="row">`;
        
        this.students.forEach(student => {
            
            htmlContent += `
            <div class="${cardSize}" name="studentCard">
                <input type='hidden' name='students' value='${student.id}'>
                <div class="card shadow mt-3">
                    <div class="card-body row text-left pb-2">
                        <div class="col-12 col-md-3 text-center">
                            <img src="${student.profilePic}">
                        </div>
                        <div class="col card-title mt-3 mt-md-0 ml-md-3 text-center text-md-left">
                            <span style="font-size: 1.1rem;">
                                ${student.firstNameEng} ${student.lastNameEng} (${student.firstNameHeb} ${student.lastNameHeb})
                            </span>
                            <div style="font-size:0.9rem; color:#5e5e5e">${student.studentId}</div>
                            <div style="font-size:0.9rem; color:#5e5e5e">${student.email}</div>
                            <div>
                                <select name='studentsCoursesIds' data-student-id='${student.id}' class='mt-3' data-style='studentsCourseIds' data-width='12.5rem'>`;
                                    if('courseId' in student){
                                        coursesList.forEach(course => {
                                            let optionText = `${course.number} - ${course.name}`;
                                            htmlContent += `<option value="${course.id}" data-subtext="(${course.academicPoints} pts)" ${(student.courseId == course.id ? "selected" : "")} >${optionText}</option>`;
                                        });	
                                    }
                                    else {
                                        coursesList.forEach(course => {
                                            let optionText = `${course.number} - ${course.name}`;
                                            htmlContent += `<option value="${course.id}" data-subtext="(${course.academicPoints} pts)" ${(course.id == defaultCourseId ? "selected" : "")} >${optionText}</option>`;
                                        });	
                                    }
            htmlContent += `     </select>
                            </div>
                            <button type="button" name="btnRemoveStudent" class="btn mt-2" data-id=${student.id}>
                                <i class="far fa-trash-alt"></i>
                            </button>
                        </div>                          
                    </div>
                </div>
            </div>
            `;
        });
        htmlContent += `</div>`;
        this.container.append(htmlContent);
        $(`#${this.target}Modal select`).selectpicker();
        
        $("button[name='btnRemoveStudent']").on("click", this.handleRemoveStudent.bind(this));
        $(`select[name="studentsCoursesIds"]`).on('change', this.handleCourseNumChange.bind(this));   
    }
}

class ProjectStatus {
    constructor(target) {
        let prefix = target === "addProject" ? "new_" : "";
        this.target = target;
        this.stages = {
            1 : {},
            2 : {
                requirementsDoc : false,
                firstMeeting : false
            },
            3 : {
                halfwayPresentation : false
            },
            4 : {
                finalMeeting : false,
                equipmentReturned : false,
                projectDoc : false,
                gradeStatus : false,
                posterStatus: false
            }
        }
        for (const stage in this.stages) {
            for (const status in this.stages[stage]) {
                $(`#${prefix}${status}`).on('change', this.handleChange.bind(this));   
            }
        }
     
    }
    
    getStageNumByStageName(stageName) {
        for (const stage in this.stages) {
            if (stageName in this.stages[stage])
                return stage;
        }
        return null;
    }

    updateStageNumColor(stageNum) {
        let stageDom = $(`#${this.target}Modal`).find(`div.projectStatusNumber[data-status-num='${stageNum}']`);
        for (const stageName in this.stages[stageNum]) {
            if(! this.stages[stageNum][stageName]) {
                stageDom.removeClass('completed');
                return;
            }
        }
        stageDom.addClass("completed");

    }

    initializeStageNumColors() {
        for (const stage in this.stages) {
            this.updateStageNumColor(stage);
        }
    }

    handleChange(element) {
        let isChecked = $(element.target).prop("checked");
        let stageClicked = $(element.target).attr("id");
        let stageNum = this.getStageNumByStageName(stageClicked);
        this.stages[stageNum][stageClicked] = isChecked;
        this.updateStageNumColor(stageNum);
    }
}

/* ------------------------------------------------------------------------------------- */

let youtubeVideoPublicStatus = "";

function getProjectData(id) {    
    var xmlhttp = new XMLHttpRequest();
    var url = "/Admin/Projects/"+id+"/json";
    xmlhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            var data = JSON.parse(this.responseText);
            editProject(data);		
        }
    };
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

function editProject(projectData) {
    $("#editProjectModal .modal-header span[name='projectTitle']").html(projectData.title);
    $("#editProjectModal .modal-header span[name='projectSemester']").html(projectData.semester);
    $("#editProjectModal .modal-header span[name='projectYear']").html(projectData.year);

    $("#editProjectForm #projectId").val(projectData.id);
    $("#editProjectForm #title").val(projectData.title);
    if ($("#editProjectForm #year option[value='"+projectData.year+"']").length == 0) {
        $("#editProjectForm #year").prepend("<option value='"+projectData.year+"' selected='selected'>"+projectData.year+"</option>");
        addedYears.push(projectData.year);
    }
    $("#editProjectForm #year").selectpicker('val', projectData.year);	
    $("#editProjectForm #semester").selectpicker('val', projectData.semester);	
    $("#editProjectForm #comments").val(projectData.comments);
    $("#editProjectForm #grade").val(projectData.grade);
    
    // get rid of <img> tag in profilePic and replace it only with the src
    projectData.students.forEach(student => {
        let profilePicSrc = $(student.profilePic).attr("src");
        student.profilePic = profilePicSrc;
    });
    editProjectStudentList.setNewStudents(projectData.students);

    
    // clear supervisors and set project's supervisors
    $("#editProjectForm #supervisor1").selectpicker('val', '')
    $("#editProjectForm #supervisor2").selectpicker('val', '')
    $("#editProjectForm #supervisor3").selectpicker('val', '')
    
    projectData.supervisors.forEach(function (supervisor, index) {
        $("#editProjectForm #supervisor"+(index+1)).selectpicker('val', supervisor.id);
    });
    
    // fill in project status checkboxes
    $('#editProjectForm #requirementsDoc').prop('checked', projectData.requirementsDoc).trigger("change"); 
    $('#editProjectForm #firstMeeting').prop('checked', projectData.firstMeeting).trigger("change"); 
    $('#editProjectForm #halfwayPresentation').prop('checked', projectData.halfwayPresentation).trigger("change"); 
    $('#editProjectForm #finalMeeting').prop('checked', projectData.finalMeeting).trigger("change"); 
    $('#editProjectForm #equipmentReturned').prop('checked', projectData.equipmentReturned).trigger("change"); 
    $('#editProjectForm #projectDoc').prop('checked', projectData.projectDoc).trigger("change"); 
    $('#editProjectForm #gradeStatus').prop('checked', projectData.gradeStatus).trigger("change"); 
    $('#editProjectForm #posterStatus').prop('checked', projectData.posterStatus).trigger("change");

    // project doc
    youtubeVideoPublicStatus = projectData.youtubeVideoPublicStatus;
    if (projectData.youtubeVideo && projectData.youtubeProcessingStatus == 'processed') {
        $("#projectDocTab div[name='content']").show();
        $("#projectDocTab div[name='emptyContentMessage']").hide();

        $("#editProjectForm #projectDocImageDiv div[name='view']").html(`<img src="/static/project_doc/image/${projectData.projectDocImage}" style="max-height:150px;object-fit: scale-down;cursor:pointer" data-toggle="modal" data-target="#projectDocImgModal">`);
        $("#enlargedProejctDocImg").html(`<img src="/static/project_doc/image/${projectData.projectDocImage}" style="max-height: 100vh;max-width: 1000px; width:100%">`);        
        $("#frmProjectDocVideo").attr("src", `https://www.youtube.com/embed/${projectData.youtubeVideo}?rel=0&autoplay=0&mute=0`)        
        $("#editProjectForm #reportDiv div[name='view']").html(`<a href="/static/project_doc/report/${projectData.report}" class="btn btn-outline-primary" target="_blank">See Report</a>`);
        $("#editProjectForm #presentationDiv div[name='view']").html(`<a href="/static/project_doc/presentation/${projectData.presentation}" class="btn btn-outline-primary" target="_blank">See Presentation</a>`);
        if (projectData.code) {
            $("#editProjectForm #codeDiv div[name='view']").html(`<a href="/static/project_doc/code/${projectData.code}" class="btn btn-outline-primary" target="_blank">See Code</a>`);
        }
        else {
            $("#editProjectForm #codeDiv div[name='view']").html(`<span class="badge shadow-sm" style="padding: .5rem 1rem;background-color: #f6f6f6;border-radius: 1.25rem;color: #2b1b41;line-height: 1.5;">No Code</span>`);
        }
        $("#editProjectForm #abstract").val(projectData.abstract);
        $("#editProjectForm #githubLink").val(projectData.githubLink);
        
        if ( projectData.projectDocApproved ) {
            $("#editProjectForm .nav-tabs a[href='#projectDocTab'] span[name='draft']").hide();
            $("#editProjectForm .nav-tabs a[href='#projectDocTab'] span[name='approved']").show();
            $("div[name='projectDocApproved']").hide();
            $("div[name='projectDocEditableByStudents']").show();
            $('#editProjectForm #projectDocEditableByStudents').prop('checked', projectData.projectDocEditableByStudents).trigger("change");
        }
        else {
            $("#editProjectForm .nav-tabs a[href='#projectDocTab'] span[name='approved']").hide();
            $("#editProjectForm .nav-tabs a[href='#projectDocTab'] span[name='draft']").show();
            $("div[name='projectDocApproved']").show();
            $("#editProjectForm #projectDocApproved").prop("checked", false);
            $("div[name='projectDocEditableByStudents']").hide();
        }
    }
    else {
        $("#editProjectForm .nav-tabs a[href='#projectDocTab'] span[name='draft']").hide();
        $("#editProjectForm .nav-tabs a[href='#projectDocTab'] span[name='approved']").hide();
        $("#projectDocTab div[name='content']").hide();
        $("#projectDocTab div[name='emptyContentMessage']").show();
    }

    // poster
    $('#editProjectForm #posterEditableByStudents').prop('checked', projectData.posterEditableByStudents).trigger("change");
    if (projectData.posterStatus) {
        $("#posterTab div[name='content']").show();
        $("#posterTab div[name='emptyContentMessage']").hide();        
        $('#editProjectForm #posterTab a').attr("href", `/static/project_doc/poster/${projectData.poster}`);
    }
    else {
        $("#posterTab div[name='content']").hide();
        $("#posterTab div[name='emptyContentMessage']").show();
    }

    $("#editProjectModal a[href='#statusTab']").trigger("click");
    
    $('#editProjectModal select').selectpicker();
    $("#editProjectModal").modal("show");
}

$(document).on("click","#editProjectModal button[name='btnAddStudents']", function(e) {
    studentsTable.open("editProject", editProjectStudentList.students);
});	 

// fill in gradeStatus checkbox automatically when user inputs a grade
$('#editProjectForm #grade').keyup(function() {
    $('#editProjectForm #gradeStatus').prop('checked', $(this).val().trim()).trigger("change");
});


/* show file name in the input box when selecting a file */
$("input[type='file'").on('change',function(){
    let fileName = $(this).val().split('\\').pop(); 
    $(this).parent().find('.custom-file-label').html(fileName);
})

$("#projectDocImageDiv, #reportDiv, #presentationDiv, #codeDiv").find("div[name='header'] button").on("click", function(e) {            
    if ($(this).text().includes("Cancel")) {
        cancelProjectDocEdit(this);
    }
    else {
        $(this).text("(Cancel edit)");
        $(this).parent().parent().find("div[name='view']").hide();
        $(this).parent().parent().find("div[name='edit']").show();
    }
});	 

function cancelProjectDocEdit(editBtnElement) {
    $(editBtnElement).text("(Edit)");
    $(editBtnElement).parent().parent().find("input[type='file']").val("");
    $(editBtnElement).parent().parent().find("input[type='file']").next('.custom-file-label').html("Choose file");
    $(editBtnElement).parent().parent().find("div[name='view']").show();
    $(editBtnElement).parent().parent().find("div[name='edit']").hide();
}

function editProjectDocItem(editBtnElement){
    $(editBtnElement).text("(Cancel edit)");
    $(editBtnElement).parent().parent().find("div[name='view']").hide();
    $(editBtnElement).parent().parent().find("div[name='edit']").show();
}

$('#editProjectModal').on('hide.bs.modal', function() {
    $("#editProjectModal div[name='errorMessage']").hide();
    $("#editProjectModal .is-invalid").each(function() {
        $(this).removeClass("is-invalid");
    })
    addedYears.forEach( function(year){
        $(`#editProjectForm #year option[value='${year}']`).remove();
    });
    addedYears = [];
    $("#frmProjectDocVideo").attr("src", "");
    $("#projectDocVideoLoading").show();
    $("#editProjectForm #image").val("");
    $("#editProjectForm #image").next('.custom-file-label').html("Choose file");


    $("#projectDocImageDiv, #reportDiv, #presentationDiv, #codeDiv").find("div[name='header'] button").each(function() {            
        cancelProjectDocEdit(this);
    });
});

var addedYears = [];

$('#frmProjectDocVideo').on("load", function () {
    if($(this).attr("src")) {
        $("#projectDocVideoLoading").hide();
        $("#frmProjectDocVideo").show();
    }
});

$(function () {
    $('[data-toggle="tooltip"]').tooltip()
})
$("#editProjectModal #projectDoc").next("label").attr({
    "data-toggle": "tooltip", 
    "title": "מסומן אוטומטית כאשר דף הפרוייקט מאושר",
    "data-placement": "left"
});

$("#editProjectModal #gradeStatus").next("label").attr({
    "data-toggle": "tooltip", 
    "title": "מסומן אוטומטית כאשר מוזן ציון לפרוייקט",
    "data-placement": "left"
});

$("#editProjectModal #posterStatus").next("label").attr({
    "data-toggle": "tooltip", 
    "title": "מסומן אוטומטית כאשר נשלח פוסטר",
    "data-placement": "left"
});


/* -----------------------------------  Send editForm using ajax  ----------------------------------- */
let editProjectRequest = new XMLHttpRequest();
editProjectRequest.responseType = 'json'

editProjectRequest.addEventListener('load', function(e) {
    let response = editProjectRequest.response;

    if (response['status'] == 'error') {
        $("#btnSavingEditProjectForm").hide();
        $("#submitEditForm").show();
        $("div#editProjectMessages").append(`<div class="alert alert-danger m-0">There was an error, see details below.</div>`)
        for(let field in response['errors']) {
            if (field == "csrf_token") {
                $("div#editProjectMessages").append(`<div class="alert alert-danger m-0">CSRF token expired, please reload the page.</div>`)
            }
            else {
                $(`#${field}`).addClass("is-invalid");
                $(`#${field}`).parent().find(`div[name='invalidFeedback']`).empty();
                $(`#${field}`).parent().find(`div[name='infoText']`).hide();
                for (let error of response['errors'][field]) {
                    $(`#${field}`).parent().find(`div[name='invalidFeedback']`).append(`<span>${error}</span>`);
                }
                $(`#${field}`).parent().find(`div[name='invalidFeedback']`).fadeIn();
            }
        }
        $("div#editProjectMessages").fadeIn();
        $("#editProjectModal").animate({ scrollTop: 0 }, 600);
        
    }
    else if (response['status'] == 'noCourseNumbers') {
        $("#btnSavingEditProjectForm").hide();
        $("#submitEditForm").show();
        $("div#editProjectMessages").append(`<div class="alert alert-danger m-0">Error: students can't be added to a project without a course number.</div>`)
        $("div#editProjectMessages").fadeIn();
        $("#editProjectModal").animate({ scrollTop: 0 }, 600);
    }
    else if (response['status'] == 'studentIsCurrentlyUploading') {
        $("#btnSavingEditProjectForm").hide();
        $("#submitEditForm").show();
        $("div#editProjectMessages").append(`<div class="alert alert-danger m-0">Error: couldn't approve project doc, there is a video currently being uploaded to youtube.</div>`)
        $("div#editProjectMessages").fadeIn();
        $("#editProjectModal").animate({ scrollTop: 0 }, 600);
    }
    else if (response['status'] == 'videoIsRequired') {
        $("#btnSavingEditProjectForm").hide();
        $("#submitEditForm").show();
        $("div#editProjectMessages").append(`<div class="alert alert-danger m-0">Error: couldn't approve project doc, video is missing.</div>`)
        $("div#editProjectMessages").fadeIn();
        $("#editProjectModal").animate({ scrollTop: 0 }, 600);
    }
    else if (response['status'] == 'projectIdNotFound') {
        $("#btnSavingEditProjectForm").hide();
        $("#submitEditForm").show();
        $("div#editProjectMessages").append(`<div class="alert alert-danger m-0">Error: couldn't find project with id '${response['id']}' in the db.</div>`);
        $("div#editProjectMessages").fadeIn();
        $("#editProjectModal").animate({ scrollTop: 0 }, 600);
    }
    else if (response['status'] == 'fileTooLarge') {
        $("#btnSavingEditProjectForm").hide();
        $("#submitEditForm").show();
        $("div#editProjectMessages").append(`<div class="alert alert-danger">Error: the file you are trying to send is too large.</div>`);
        $("div#editProjectMessages").fadeIn();
        $("#editProjectModal").animate({ scrollTop: 0 }, 600);
    }
    else if (response['status'] == 'success') {
        if ($("#projectDocApproved").is(":checked") && youtubeVideoPublicStatus != "success") {
            $('#editProjectModal').modal("hide");
            $("#settingVideoPublicModal").modal({backdrop: 'static', keyboard: false});
            checkVideoPublicStatus();
        }
        else {
            let redirectURL = window.location.pathname;
            window.location.replace(redirectURL);
        }
    }
});


$("#editProjectForm").submit(function( event ) {
    event.preventDefault();
    $("#editProjectForm .is-invalid").each(function() {
        $(this).removeClass("is-invalid");
    })
    $("div#editProjectMessages").empty();
    $("div#editProjectMessages").hide();
    $("#submitEditForm").hide();
    $("#btnSavingEditProjectForm").show();
    editProjectRequest.open('post', $("#editProjectForm").attr("action")); 
    var formData = new FormData(document.getElementById("editProjectForm"));
    editProjectRequest.send(formData);
});


/* -----------------------------------  END OF - Send editForm using ajax  ----------------------------------- */




/* -----------------------------------  Check status of setting youtube video public  ----------------------------------- */
function checkVideoPublicStatus() { 
    let afterVideoPublicChangeAttempt = false;
    $("#settingVideoPublicModal div[name='settingPublicFailed']").hide();
    $("#settingVideoPublicModal div[name='settingVideoPublic']").show();
    let checkVideoPublicStatusInterval = setInterval(function() {
        let projectId = $("#editProjectForm #projectId").val();

        $.post(`/Admin/Projects/${projectId}/YoutubeVideoPublicStatus`, {"afterChangeAttempt": afterVideoPublicChangeAttempt}, function(data, status){
            if (data.status == "success") {
                clearInterval(checkVideoPublicStatusInterval);
                let redirectURL = window.location.pathname;
                window.location.replace(redirectURL);
            }
            else if (data.status == "failed") {
                clearInterval(checkVideoPublicStatusInterval);
                $("#settingVideoPublicModal div[name='settingVideoPublic']").hide();
                $("#settingVideoPublicModal div[name='settingPublicFailed']").fadeIn();
            }
            afterVideoPublicChangeAttempt = true;
        });
    }, 4000);
}
/* -----------------------------------  END OF - Check status of setting youtube video public  ----------------------------------- */


$('#addStudentsModal').on('hide.bs.modal', function() {
    $("#addStudentsModal .btn-clear-table-filters").click();
});