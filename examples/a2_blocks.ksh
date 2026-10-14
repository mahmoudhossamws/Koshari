let x = 10;
{
    let x = 20;
    {
        let x = 30;
        print x;
    }
    print x;
}
print x;
{
    # There is no local x here, so assignment updates the global x.
    x += 1;
}
print x;
