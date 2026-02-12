<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en-US">

<head>
    <meta http-equiv="X-UA-Compatible" content="IE=10" />
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="copyright" content="Copyright(c) 2005-2021 Trimble Inc." />
    <meta name="description" content="Trimble IP Enabled Geomatics GNSS Receiver" />
    <meta name="keywords" content="GPS, GLONASS, Galileo, BeiDou, QZSS, IRNSS, SBAS, GNSS, Trimble, Geomatics, Infrastructure, Survey, VRS, Construction, SPS" />
    
    <link rel="shortcut icon" href="CACHEDIR3473312567/favicon.ico" />

    <!-- Device Detection and Viewport Configuration -->
    <script language="javascript">
        var trmbTop = self;
        {
            self.name = "trmbTop";
            trmbTop.screenHeight = screen.height;
            trmbTop.screenWidth = screen.width;
            var smallest = screen.height < screen.width ? screen.height : screen.width;
            trmbTop.tinyScreen = (smallest < 650);
            
            String.prototype.has = function(s) {
                return this.indexOf(s) > -1;
            };
            
            agent = navigator.userAgent;
            var isMiniDevice = (agent.has("Mobile") || 
                               agent.has("Phone") || 
                               (agent.has("Android") && !agent.has("Tablet") && !agent.has("Nexus 7")) || 
                               agent.has("Fennec") || 
                               agent.has("Windows CE") || 
                               agent.has("Opera Mobi") || 
                               agent.has("Opera Mini") || 
                               agent.has("BlackBerry")) && 
                              (!agent.has("iPad"));
            
            var cgiArgs = self.location.search;
            trmbTop.miniBrowser = (isMiniDevice || cgiArgs.has('mini')) && !cgiArgs.has('full');
            
            if (trmbTop.miniBrowser)
                document.writeln('<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0"/>');
            else
                document.writeln('<meta name="viewport" content="width=device-width,initial-scale=1.0,minimum-scale=0.5,maximum-scale=5.0"/>');
            
            trmbTop.touchScreen = ('createTouch' in document);
        }
    </script>

    <!-- External JavaScript Libraries -->
    <script type="text/javascript" src="CACHEDIR3473312567/js/jquery.js"></script>
    <script type="text/javascript" src="CACHEDIR3473312567/js/ajax.js"></script>
    <script type="text/javascript" src="CACHEDIR3473312567/js/ajax2.js"></script>
    <script type="text/javascript" src="CACHEDIR3473312567/js/menu.js"></script>

    <!-- Main Application Functions -->
    <script language="javascript">
        // Menu visibility controls
        function hideMenu() {
            jQuery('#idMenuDiv').fadeOut(1000);
            jQuery('#idMenuInDiv').fadeIn(1000);
        }

        function showMenu() {
            jQuery('#idMenuDiv').fadeIn(1000);
            jQuery('#idMenuInDiv').fadeOut(1000);
        }

        // Floating div controls
        function hideFloatingDiv(quick) {
            if (quick)
                jQuery('#idFloatingDiv').hide();
            else
                jQuery('#idFloatingDiv').fadeOut(500);
        }

        function showFloatingDiv(quick) {
            if (quick)
                jQuery('#idFloatingDiv').hide();
            else
                jQuery('#idFloatingDiv').fadeIn(500);
        }

        // Startup initialization
        function startup() {
            if (!setupTrmbTop(startup))
                return;
            
            menuDiv = self.document.getElementById('idMenuDiv');
            menuInDiv = self.document.getElementById('idMenuInDiv');
            systemDiv = self.document.getElementById('idSystemDiv');
            floatingDiv = self.document.getElementById('idFloatingDiv');
            
            if ((rxBrand != 0 && rxBrand != 10) || trmbTop.optionData.OptMINI_GUI_SUPPORT == 'FALSE') {
                trmbTop.miniBrowser = false;
            }
            
            if (trmbTop.miniBrowser) {
                retrieveFramesSize(window.frames.main.document);
                window.frames.main.location = cacheDirPath('miniMain.html');
                
                if (window.addEventListener) {
                    var supportsOrientationChange = ("onorientationchange" in window);
                    var orientationEvent = supportsOrientationChange ? "orientationchange" : "resize";
                    window.addEventListener(orientationEvent, function() {
                        updateOrientation();
                    }, false);
                }
            } else {
                loadFull();
            }
        }

        function loadFull() {
            trmbTop.miniBrowser = false;
            window.frames.main.location = cacheDirPath('main.html');
        }

        // Reboot and reconnection handling
        var rebootCounter;

        function showReboot(cgiUrl, rebootCounterOverride) {
            if (rebootCounterOverride != undefined)
                rebootCounter = rebootCounterOverride;
            else
                rebootCounter = 60;
            
            self.main.location = cacheDirPath('blankpage.html');
            menuDiv.style.visibility = menuInDiv.style.visibility = systemDiv.style.visibility = 'hidden';
            
            var div = floatingDiv;
            div.innerHTML = '<div align="center"' +
                           ' style="font-size:10pt;font-weight:bold">' +
                           getString('WaitForReconnect') + '<br/><b id="rebootCount"></b>' +
                           ' ' + getString('secAbbr') + '<br/>' +
                           getString('WaitForReconnect2') + '<br/>' +
                           makeButton('', getString('Reconnect'), 'trmbTop.reconnect()') +
                           '</div>';
            
            div.style.position = 'absolute';
            div.style.left = 25;
            div.style.top = 25;
            div.style.width = 'auto';
            div.style.height = 'auto';
            div.style.right = '';
            div.style.textAlign = 'center';
            div.style.padding = '10px';
            
            showFloatingDiv();
            rebootCountdown();
            
            if (cgiUrl)
                setTimeout('getXmlAsync( "' + topUrlPath(cgiUrl) + '")', 2000);
        }

        function rebootCountdown() {
            --rebootCounter;
            
            if (rebootCounter == 0)
                reconnect();
            else {
                toInnerHtml('rebootCount', rebootCounter);
                setTimeout('rebootCountdown()', 1000);
            }
        }

        function reconnect() {
            self.document.location.reload(true);
        }

        // Communication failure handling
        function hideCommFailure() {
            jQuery('#commFailDiv').hide();
        }

        function showCommFailure(message) {
            var d = jQuery('#commFailDiv');
            d.css({right: '25px', bottom: '25px'});
            d.html(message);
            d.show();
        }

        // Cleanup on page unload
        function onUnload() {
            var now = new Date();
            var then = new Date(now.getTime() + 10000);
            document.cookie = 'quickStart=yes' + ';expires=' + then.toGMTString() + ';SameSite=Lax';
        }
    </script>
</head>

<body onload="startup()" 
      onunload="onUnload()" 
      style="overflow:hidden" 
      leftmargin="0" 
      rightmargin="0" 
      topmargin="0" 
      bottommargin="0">

    <!-- Main Content Frame -->
    <iframe name="main" 
            id="main" 
            width="100%" 
            height="100%" 
            frameborder="0">
    </iframe>

    <!-- Menu Overlay -->
    <div id="idMenuDiv" 
         class="menuDiv shadow5" 
         style="display:none; position:absolute; top:5; left:0; z-index:2; width:209; height:90%; border-radius:10px">
    </div>

    <!-- Menu Toggle Button -->
    <div id="idMenuInDiv" 
         class="menuDiv shadow3" 
         style="display:none; position:absolute; top:0; left:0; z-index:1; width:15; height:52; border-radius:5px">
    </div>

    <!-- System Status Div -->
    <div id="idSystemDiv" 
         class="systemDiv shadow3" 
         style="display:none; position:absolute; top:3; right:5; z-index:1; width:auto; height:auto; border-radius:5px;">
    </div>

    <!-- Floating Message Container -->
    <div id="idFloatingDiv" 
         class="floatingDiv shadow5" 
         frameborder="yes" 
         style="display:none; position:absolute; z-index:2; overflow:hidden;">
    </div>

    <!-- Communication Failure Message -->
    <div id="commFailDiv" 
         class="floatingDiv shadow5" 
         frameborder="yes" 
         style="display:none; position:absolute; z-index:2; overflow:hidden;">
    </div>

</body>

</html>