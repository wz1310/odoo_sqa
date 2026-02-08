odoo.define('sh_odoo_web_console.sh_odoo_web_console', function (require) {
    "use strict";

    $(document).ready(function(){
        function apply_style(){
            let numberWidth = 40;
            let $shStyle = $('.sh_odoo_web_console_style');
            let $gutter = $('.ace_editor .ace_gutter-layer');
            if($shStyle.length){
                if($gutter.length){
                    numberWidth = $gutter.width();
                }
                $shStyle.html(`
                    <style>
                        :root{
                            --sh-number-width: ${numberWidth}px;
                        }
                    </style>
                `);
            }
        }

        //Make sure the line width is correct
        setTimeout(function(){ apply_style(); }, 300);
        setTimeout(function(){ apply_style(); }, 1000);
        setTimeout(function(){ apply_style(); }, 3000);
    });
});
