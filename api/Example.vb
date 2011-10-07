Module Example
    Private Sub hello()
        Context.start("saying hello")
        Console.Write("hello ")
        Threading.Thread.Sleep(1000)
        Context.endok("saying hello")
    End Sub

    Private Sub world()
        Context.start("saying world")
        Console.WriteLine("world")
        Threading.Thread.Sleep(2000)
        Context.endok("saying world")
    End Sub

    Sub Main()
        Context.setLog("output.vb.ctext")
        Context.start("running program")
        hello()
        world()
        Context.endok("running program")
        Context.closeLog()
    End Sub
End Module