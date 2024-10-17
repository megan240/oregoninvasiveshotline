$(document).ready(function(){
    // bail out if the browser doesn't support the filereader
    try {
        new FileReader();
    } catch(e) {
        return;
    }

    // whenever an image is selected, generate a preview of it with scaling
    $('#images').on('change', 'input[type="file"]', function(e){
        var files = $(this).get(0).files;
        $('#previews').html("");

        var MAX_WIDTH = 100;
        var MAX_HEIGHT = 100;

        for(var i = 0; i < files.length; i++){
            var file = files[i];
            if(file){
                var reader = new FileReader();
                reader.onloadend = function(index, element, e) {
                    var append_to = element.closest(".formset-row").find(".preview");
                    var encoded_image = element.closest(".formset-row").find(".datauri");
                    var preview = $("<img />");
                    append_to.html(preview);
                    preview.attr('src', this.result);

                    preview.on("load", function(){
                        var img = preview.get(0);

                        // Scaling logic to maintain aspect ratio
                        var width = img.width;
                        var height = img.height;
                        var widthScale = MAX_WIDTH / width;
                        var heightScale = MAX_HEIGHT / height;
                        var scale = Math.min(widthScale, heightScale);

                        // If image is larger than the max dimensions, scale it down
                        if (scale < 1) {
                            width = width * scale;
                            height = height * scale;
                        }

                        // Apply the scaled dimensions to the preview image
                        preview.css({
                            'width': width + 'px',
                            'height': height + 'px',
                            'object-fit': 'contain'  // Ensures the aspect ratio is maintained
                        });

                        encoded_image.val(img.src);  // No resizing the actual image
                        element.remove(); // remove the input element
                    });
                }.bind(reader, i, $(this));
                reader.readAsDataURL(file);
            }
        }
    });
});
