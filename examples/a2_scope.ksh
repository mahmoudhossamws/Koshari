let x = 10;

function show() {
    print x;
}

function caller() {
    let x = 20;
    show();
}

caller();
