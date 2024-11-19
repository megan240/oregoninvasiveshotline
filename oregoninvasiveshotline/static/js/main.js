$(document).ready(function(){
    /* when a new formset is to be added, clone the first formset-row (which
     * acts as a template), replace all the __prefix__ placeholders, and append
     * it after the last formset-row. Make sure to update the management form
     * TOTAL_FORMS field
     */
    $('.formset-adder').on('click', function(e){
        e.preventDefault();
        var formset = $(this).closest(".formset");
        var copy = formset.find('.formset-row:first').clone(true, true);
        // figure out what number to use for this new formset
        var n = formset.find('.formset-row').length - 1; // minus 1 because of the hidden empty_form
        // update the name/ids on the clone
        copy.html(copy.html().replace(/__prefix__/g, n))
        // add it to the formset
        formset.find('.formset-row:last').after(copy);
        copy.show()

        // update the django management form so it knows a new form was added
        var total_forms = formset.find('*[name$="TOTAL_FORMS"]');
        total_forms.val(1+parseInt(total_forms.val(), 10))

        // fire off a custom event to notify listeners that something was added
        $(this).trigger("formset:added");
    })

    // make the deleted formset rows pretty when they are deleted
    $('.formset').on('click', '.delete-field input[type=checkbox]', function(e){
        $(this).closest('.formset-row').toggleClass("formset-row-deleted");
    });
    $('.formset-row:has(.delete-field input[type=checkbox]:checked)').addClass("formset-row-deleted")

    // tab handling stuff

    $('.nav-tabs a').click(function (e) {
        if($(this).attr("href").substring(0, 1) == "#"){
            console.log("here")
            Cookies.set('tab', $(this).attr('href'), {path: window.location.pathname})
            e.preventDefault()
            $(this).tab('show')
        }
    })

    $('.nav-tabs a:first, .nav-tabs a[href="' + Cookies.get('tab') + '"]').click();
});

/* This exists solely to avoid duplicating the icon dimension information
 * everywhere. If you are to change this make sure you update
 * `oregoninvasiveshotline/reports/views.py:icon`
 */
function generateIcon(url){
    return {
        url: url,
        size: new google.maps.Size(30, 45),
        origin: new google.maps.Point(0,0),
        anchor: new google.maps.Point(15,45),
    }
}

/*Just DRY up the Google map option stuff */
function getDefaultMapOptions(){
    var mapOptions = {
        center: {
            // this is approximately the center of oregon, and looks good at zoom level 7
            lat: 44, lng: -120.578333
        },
        zoom: 7,
        streetViewControl: false,
    };

    // if the zoom and center have been defined in a cookie, use that for the
    // initial map options
    if(Cookies.get("zoom") != undefined){
        mapOptions.zoom = parseInt(Cookies.get("zoom"), 10)
    }
    if(Cookies.get("center") != undefined){
        var parts = Cookies.get("center").split(",")
        mapOptions.center.lat = parseFloat(parts[0])
        mapOptions.center.lng = parseFloat(parts[1])
    }

    return mapOptions;
}

// Code to allow the Hamburger Menu to be functional on small pages
// const smallNavToggle = document.querySelector('#navbar-toggler');
const smallNavToggle = document.querySelector('#small-nav-bar-div');
// const theSmallHeaderElement = document.querySelector('#small-screen-header nav');
const theSmallNavElement = document.querySelector('#small-nav-bar');
const theMainElement = document.querySelector('#main');


const toggleCollapser = () => {
    const lengthOfArr = theSmallNavElement.getAttribute("class");
    // if uncollapsed, let's collapse it by removing class="uncollapsed-block"
    // and adding class="collapsed-block"
    if(lengthOfArr.includes("uncollapsed-block")){ // note "un..." evaluated first
        theMainElement.classList.remove("collapsed-block");
        theMainElement.classList.add("uncollapsed-block");
        theSmallNavElement.classList.remove("uncollapsed-block");
        theSmallNavElement.classList.add("collapsed-block");
    }
    else if(lengthOfArr.includes("collapsed-block")){
        theMainElement.classList.remove("uncollapsed-block");
        theMainElement.classList.add("collapsed-block");
        theSmallNavElement.classList.remove("collapsed-block");
        theSmallNavElement.classList.add("uncollapsed-block");
    }
    else{
        console.log("error");
    }
};

smallNavToggle.addEventListener('click', toggleCollapser);

const getItemList = document.querySelectorAll('.sm-nav-list-item a');

for(let i = 0; i < getItemList.length; i++){
    getItemList[i].addEventListener('click', toggleCollapser);
}