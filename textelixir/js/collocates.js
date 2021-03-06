var copyBtn = document.querySelector('#copy_btn');
copyBtn.addEventListener('click', function () {
    window.getSelection().removeAllRanges();
    var urlField = document.querySelector('table');
        
    // create a Range object
    var range = document.createRange();  
    // set the Node to select the "range"
    range.selectNode(urlField);
    // add the Range to the set of window selections
    window.getSelection().addRange(range);
        
    // execute 'copy', can't 'cut' in this case
    document.execCommand('copy');
}, false);

function sortAlpha(n) {
    let startTime = new Date();
    let body = document.querySelector('body');
    // change the cursor to loading
    body.classList.add('waiting');
    setTimeout(() => {
        var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
        table = document.getElementById("table");
        switching = true;
        //Set the sorting direction to ascending:
        dir = "asc"; 
        /*Make a loop that will continue until
        no switching has been done:*/
        while (switching) {
        //start by saying: no switching is done:
            switching = false;
            rows = table.rows;
            /*Loop through all table rows (except the
            first, which contains table headers):*/
            for (i = 1; i < (rows.length - 1); i++) {
                //start by saying there should be no switching:
                shouldSwitch = false;
                /*Get the two elements you want to compare,
                one from current row and one from the next:*/
                x = rows[i].getElementsByTagName("TD")[n];
                y = rows[i + 1].getElementsByTagName("TD")[n];
                /*check if the two rows should switch place,
                based on the direction, asc or desc:*/
                if (dir == "asc") {
                    if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                        //if so, mark as a switch and break the loop:
                        shouldSwitch= true;
                        break;
                    }
                } else if (dir == "desc") {
                    if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                        //if so, mark as a switch and break the loop:
                        shouldSwitch = true;
                        break;
                    }
                }
            }
            if (shouldSwitch) {
                /*If a switch has been marked, make the switch
                and mark that a switch has been done:*/
                rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                switching = true;
                //Each time a switch is done, increase this count by 1:
                switchcount ++;      
            } else {
                /*If no switching has been done AND the direction is "asc",
                set the direction to "desc" and run the while loop again.*/
                if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
                }
            }
        }
    // change the cursor to a pointer
    body.classList.remove('waiting');
    // time test
    let endTime = new Date();
    let timeDiff = endTime - startTime;
    timeDiff /= 1000;
    let rows_length = document.querySelectorAll('tr').length;
    // console.log(`${rows_length} took ${timeDiff} seconds to load alpha`);
    }, 50)
}


function sortNum(n) {
    let startTime = new Date();
    let body = document.querySelector('body');
  //   change the cursor to loading
    body.classList.add('waiting');
    setTimeout(() => {
      var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
      table = document.getElementById("table");
      switching = true;
      //Set the sorting direction to ascending:
      dir = "asc"; 
      /*Make a loop that will continue until
      no switching has been done:*/
      while (switching) {
        //start by saying: no switching is done:
        switching = false;
        rows = table.rows;
        /*Loop through all table rows (except the
        first, which contains table headers):*/
          for (i = 1; i < (rows.length - 1); i++) {
              //start by saying there should be no switching:
              shouldSwitch = false;
              /*Get the two elements you want to compare,
              one from current row and one from the next:*/
              x = rows[i].getElementsByTagName("TD")[n];
              y = rows[i + 1].getElementsByTagName("TD")[n];
              //check if the two rows should switch place:
              
              if (dir == "asc") {
                  if (Number(x.innerHTML) > Number(y.innerHTML)) {
                  //if so, mark as a switch and break the loop:
                  shouldSwitch = true;
                  break;
                  }
              } else if (dir == "desc") {
                  if (Number(x.innerHTML) < Number(y.innerHTML)) {
                  //if so, mark as a switch and break the loop:
                  shouldSwitch = true;
                  break;
                  }
              }
          }
          if (shouldSwitch) {
          /*If a switch has been marked, make the switch
          and mark that a switch has been done:*/
          rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
          switching = true;
          //Each time a switch is done, increase this count by 1:
          switchcount ++;      
          } else {
          /*If no switching has been done AND the direction is "asc",
          set the direction to "desc" and run the while loop again.*/
              if (switchcount == 0 && dir == "asc") {
                  dir = "desc";
                  switching = true;
              }
          }
      }
      // change the cursor back
      body.classList.remove('waiting');
      let endTime = new Date();
      let timeDiff = endTime - startTime;
      timeDiff /= 1000;
      let rows_length = document.querySelectorAll('tr').length;
  
      console.log(`${rows_length} rows took ${timeDiff} seconds to load nums`);
    }, 50)
    
  
}
