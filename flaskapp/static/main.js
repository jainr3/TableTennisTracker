function enableButton()
{
    var selectelem = document.getElementById('dropdown_points');
    var btnelem = document.getElementById('start_newgame');
    btnelem.disabled = !selectelem.value;
}