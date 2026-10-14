# The lookup chain also determines which variable assignment changes.
let x = 10;
function increment() {
    x += 1;
}
function caller() {
    let x = 20;
    increment();
    print x;
}
caller();
print x;
