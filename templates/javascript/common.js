const buildStorageKey = (suffix) => window.location.href.split('?')[0] + '#' + suffix;

const saveMark = ()=>{
    let marks = $('.mark').map(function(){
        let overridedMark = $("#"+ this.id + "-locked").html();
        console.log(overridedMark);
        return {id: this.id.replace('mark-',''), mark: $(this).val(), overridedMark: overridedMark};
    }).get(); 

    try {
        localStorage.setItem(buildStorageKey('marks'), JSON.stringify(marks));
        console.log("Mark saved in localStorage!");
    } catch(e) {
        console.error("Failed to save mark to localStorage:", e);
    }

    // Also attempt server-side save (works when running with Flask; silently ignored on static hosting)
    $.ajax({                    
        data: JSON.stringify({"type":"mark","data": marks}),
        type: "POST",
        dataType: "json",
        contentType: "application/json;charset=utf-8",
        success: function(returnData){
            console.log("Mark saved in server!");
        },
        error: function(){
            // Server not available (e.g. GitHub Pages static hosting) – localStorage save is sufficient
        }
    });                
    return marks;
};


const loadMark = (callback)=>{
    // Try localStorage first (works on both static and dynamic hosting)
    const stored = localStorage.getItem(buildStorageKey('marks'));
    if (stored) {
        try {
            const returnData = JSON.parse(stored);
            returnData.forEach(element => {
                $("#mark-"+ element.id).val(element.mark);
                if(element.overridedMark)
                    $("#mark-"+ element.id + "-locked").html(element.overridedMark);
            });
            console.log("Loaded mark from localStorage");
            if(callback) callback();
            return;
        } catch(e) {
            console.warn("Failed to parse marks from localStorage:", e);
        }
    }

    // Fall back to static mark.json (present after notebooks are run)
    $.ajax({
        url: $(location).attr('href').replace('index.html',"mark.json"),                   
        type: "GET",
        dataType: "json",
        contentType: "application/json;charset=utf-8",
        success: function(returnData){            
            returnData.forEach(element => {
                $("#mark-"+ element.id).val(element.mark);
                if(element.overridedMark)
                    $("#mark-"+ element.id + "-locked").html(element.overridedMark);
            });
            console.log("Loaded mark from mark.json");
            if(callback) callback();
        },
        error: function(){
            console.log("No saved mark found");
            if(callback) callback();
        }
    });
};

const convertFormToJSON = form => {
  return $("#controlForm")
    .serializeArray()
    .reduce(function (json, { name, value }) {
      json[name] = value;
      return json;
    }, {});
}

const saveControlForm = () => {
    const formData = convertFormToJSON();
    try {
        localStorage.setItem(buildStorageKey('control'), JSON.stringify(formData));
        console.log("Control form saved in localStorage!");
    } catch(e) {
        console.error("Failed to save control form to localStorage:", e);
    }

    // Also attempt server-side save (works when running with Flask; silently ignored on static hosting)
    $.ajax({                    
        data: JSON.stringify({"type":"control", "data": formData}),
        type: "POST",
        dataType: "json",
        contentType: "application/json;charset=utf-8",
        success: function(returnData){
            console.log("Control Form saved in server!");
        },
        error: function(){
            // Server not available (e.g. GitHub Pages static hosting) – localStorage save is sufficient
        }
    }); 
};

const loadControlForm = (callback) =>{
    // Try localStorage first (works on both static and dynamic hosting)
    const stored = localStorage.getItem(buildStorageKey('control'));
    if (stored) {
        try {
            const returnData = JSON.parse(stored);
            for (let i in returnData) {
                $('#'+i).val(returnData[i]);
            }
            if(returnData.fullMark && returnData.granularity) {
                $('.mark')
                    .attr("max",returnData.fullMark)
                    .attr("step",returnData.granularity);
            }
            if(returnData.regenerate == "on"){
                $("#regenerate").attr("checked", "checked");
            }
            console.log("Loaded control form from localStorage");
            if(callback) callback();
            return;
        } catch(e) {
            console.warn("Failed to parse control form from localStorage:", e);
        }
    }

    // Fall back to static control.json (present after notebooks are run)
    $.ajax({
        url: $(location).attr('href').replace('index.html',"control.json"),                   
        type: "GET",
        dataType: "json",
        contentType: "application/json;charset=utf-8",
        success: function(returnData){
            console.log("Loaded control form from control.json");
            for (let i in returnData) {                            
                $('#'+i).val(returnData[i]);        
            }
            if(returnData.fullMark && returnData.granularity)
            {
                $('.mark')
                    .attr("max",returnData.fullMark)
                    .attr("step",returnData.granularity);
            }
            if(returnData.regenerate == "on"){
                $("#regenerate").attr("checked", "checked");    
            }
            if(callback) callback();
        },
        error: function(){
            console.log("No saved control form found");
            if(callback) callback();
        }
    });
};

const zoomImage = (callback)=>{                
    const zoom = $('#zoom').val();   

    const commonLeft =  $('#left').val();
    const commonTop = $('#top').val();
    const commonWidth = $('#width').val() ;
    const commonHeight =  $('#height').val() ;

    console.log("zoomImage", commonLeft,commonTop,commonWidth,commonHeight);

    let left, top, width, height, imageWidth, imageHeight;

    for(let b of boundingBoxes){
        left = commonLeft || b.left * zoom;
        top = commonTop || b.top * zoom;
        width = commonWidth || b.width * zoom;
        height = commonHeight || b.height * zoom;
        $('#crop-'+ b.id)
            .css('object-fit','none')
            .css('width', width + "px")
            .css('height', height + "px")
            .css('object-position', "-"+ left + "px -"+ top +"px")
            .css('transform-origin', "left top")
            .css('transform', `scale(${zoom})`);
    }
    
    if(callback) callback();
};

$(document).ready(() => {     
    loadControlForm(()=>loadMark(()=>zoomImage(()=>saveMark())));  
    
    // Function to save column visibility to cookies
    function saveColumnVisibility(columnName, isVisible) {
        document.cookie = `col-${columnName}=${isVisible}; path=/; max-age=31536000`; // 1 year
    }
    
    // Function to get column visibility from cookies
    function getColumnVisibility(columnName) {
        const name = `col-${columnName}=`;
        const decodedCookie = decodeURIComponent(document.cookie);
        const ca = decodedCookie.split(';');
        for(let i = 0; i < ca.length; i++) {
            let c = ca[i].trim();
            if (c.indexOf(name) == 0) {
                return c.substring(name.length, c.length) === 'true';
            }
        }
        return null; // No cookie found
    }
    
    // Function to update button styling based on visibility
    function updateButtonStyle(btn, isVisible) {
        if (isVisible) {
            btn.css({'background-color': '#4CAF50', 'color': 'white', 'border-color': '#45a049'});
        } else {
            btn.css({'background-color': '#f5f5f5', 'color': '#999', 'border-color': '#ccc'});
        }
    }
    
    // Handle toggle clicks
    $('a.toggle-vis, button.toggle-vis').on( 'click', function (e) {
        e.preventDefault();
        if (window.table) {
            let column = window.table.column( $(this).attr('data-column') );
            let columnName = $(this).text().toLowerCase();
            column.visible( ! column.visible() );
            updateButtonStyle($(this), column.visible());
            
            // Save to cookie
            saveColumnVisibility(columnName, column.visible());
            
            // Hide/show image controls based on Image column visibility
            if ($(this).attr('data-column') === '1' || $(this).attr('data-column') === '0') {  // Image column
                if (column.visible()) {
                    $('#imageControls').css('display', 'contents');
                    // Apply zoom settings when showing images
                    zoomImage();
                } else {
                    $('#imageControls').css('display', 'none');
                }
            }
            
            // Recalculate column widths after toggling
            window.table.columns.adjust().draw(false);
        }
    } );


    $('#dialog').dialog({ 
        autoOpen: false, show: false,
        maxHeight: $(window).height() - 100, 
        minWidth: $(window).width() - 100 ,
        resizable: true
    })

    $('.answerImage').on('click',function(e){
        e.preventDefault();
        console.log($(this).data());
        let left = $(this).data('left');
        let top = $(this).data('top');
        let width = $(this).data('width');
        let height = $(this).data('height');

        $('#left').val(left);
        $('#top').val(top);
        $('#width').val(width);
        $('#height').val(height);

        $('#dialog').dialog('open');
        $('#largeImage').attr('src', $(this).attr('src'));              
    });

    $(document).on('keyup input', '.mark', function(e) {
        let mark = e.target.value;
        $("#" + e.target.id + "-locked").html(mark);
        saveMark();
    });

    $(document).on('click', '.lock', function(e) {
        $("#" + e.target.id).html("");
        saveMark();
    });
    
    $('#controlForm').on('keyup change paste', 'input, select, textarea, radio', e => {
        console.log('Form changed:' + e.target.id +","+ e.target.name);
        saveControlForm();       
    });
    
    $('#zoom').on('change', e => {
        $('#currentZoom').html(e.target.value);
        zoomImage();
    });

    $('.changeBoundBox').on('change', e =>{             
        zoomImage();                
    });      

} );